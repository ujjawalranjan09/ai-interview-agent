"""Webhook service — CRUD operations and delivery for webhooks."""

import asyncio
import hashlib
import hmac
import json
import logging
import time
import uuid
from typing import Any, Dict, List, Optional

import httpx
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.webhook import Webhook, WebhookDelivery

logger = logging.getLogger(__name__)

# Maximum retry attempts
MAX_RETRIES = 3
RETRY_DELAY_BASE = 2  # Exponential backoff base


def generate_signature(payload: str, secret: str) -> str:
    """Generate HMAC-SHA256 signature for webhook payload."""
    return hmac.new(
        secret.encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


async def create_webhook(
    db: AsyncSession,
    name: str,
    url: str,
    events: List[str],
    user_id: uuid.UUID,
    secret: Optional[str] = None,
    organization_id: Optional[uuid.UUID] = None,
) -> Webhook:
    """Create a new webhook."""
    webhook = Webhook(
        name=name,
        url=url,
        events=events,
        secret=secret,
        created_by=user_id,
        organization_id=organization_id,
    )
    db.add(webhook)
    await db.flush()
    return webhook


async def get_webhook(db: AsyncSession, webhook_id: uuid.UUID) -> Optional[Webhook]:
    """Get a webhook by ID."""
    result = await db.execute(select(Webhook).where(Webhook.id == webhook_id))
    return result.scalar_one_or_none()


async def list_webhooks(
    db: AsyncSession,
    user_id: uuid.UUID,
    page: int = 1,
    page_size: int = 20,
) -> Dict[str, Any]:
    """List webhooks for a user."""
    query = select(Webhook).where(Webhook.created_by == user_id)
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0
    
    # Paginate
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    webhooks = list(result.scalars().all())
    
    return {
        "items": webhooks,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": (total + page_size - 1) // page_size,
    }


async def update_webhook(
    db: AsyncSession,
    webhook_id: uuid.UUID,
    name: Optional[str] = None,
    url: Optional[str] = None,
    events: Optional[List[str]] = None,
    is_active: Optional[bool] = None,
    secret: Optional[str] = None,
) -> Optional[Webhook]:
    """Update a webhook."""
    webhook = await get_webhook(db, webhook_id)
    if not webhook:
        return None
    
    if name is not None:
        webhook.name = name
    if url is not None:
        webhook.url = url
    if events is not None:
        webhook.events = events
    if is_active is not None:
        webhook.is_active = is_active
    if secret is not None:
        webhook.secret = secret
    
    await db.flush()
    return webhook


async def delete_webhook(db: AsyncSession, webhook_id: uuid.UUID) -> bool:
    """Delete a webhook."""
    webhook = await get_webhook(db, webhook_id)
    if not webhook:
        return False
    
    await db.delete(webhook)
    await db.flush()
    return True


async def trigger_webhooks(
    db: AsyncSession,
    event_type: str,
    payload: dict,
    organization_id: Optional[uuid.UUID] = None,
) -> List[WebhookDelivery]:
    """Trigger all webhooks subscribed to an event type."""
    query = select(Webhook).where(
        Webhook.is_active,
        Webhook.events.contains(event_type),
    )
    
    if organization_id:
        query = query.where(Webhook.organization_id == organization_id)
    
    result = await db.execute(query)
    webhooks = list(result.scalars().all())
    
    deliveries = []
    for webhook in webhooks:
        delivery = await deliver_webhook(webhook, event_type, payload, db)
        deliveries.append(delivery)
    
    return deliveries


async def deliver_webhook(
    webhook: Webhook,
    event_type: str,
    payload: dict,
    db: AsyncSession,
) -> WebhookDelivery:
    """Deliver a webhook with retry logic."""
    delivery = WebhookDelivery(
        webhook_id=webhook.id,
        event_type=event_type,
        payload={"event": event_type, "data": payload, "timestamp": int(time.time())},
    )
    
    headers = {
        "Content-Type": "application/json",
        "X-Webhook-Event": event_type,
        "X-Webhook-ID": str(webhook.id),
    }
    
    # Add signature if secret is set
    body = json.dumps(delivery.payload)
    if webhook.secret:
        signature = generate_signature(body, webhook.secret)
        headers["X-Webhook-Signature"] = signature
    
    success = False
    last_error = None
    status_code = None
    
    for attempt in range(MAX_RETRIES):
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(webhook.url, content=body, headers=headers)
                status_code = response.status_code
                delivery.response_body = response.text[:1000]
                
                if 200 <= response.status_code < 300:
                    success = True
                    break
                else:
                    last_error = f"HTTP {response.status_code}"
                    
        except httpx.TimeoutException:
            last_error = "Request timeout"
        except httpx.RequestError as e:
            last_error = str(e)
        except Exception as e:
            last_error = str(e)
        
        # Exponential backoff
        if attempt < MAX_RETRIES - 1:
            await asyncio.sleep(RETRY_DELAY_BASE ** attempt)
    
    delivery.success = success
    delivery.response_status = status_code
    delivery.error_message = last_error
    delivery.attempts = MAX_RETRIES if not success else attempt + 1
    
    # Update webhook status
    webhook.last_triggered_at = str(int(time.time()))
    webhook.last_status = "success" if success else "failed"
    
    if not success:
        webhook.failure_count = (webhook.failure_count or 0) + 1
        # Auto-deactivate after 10 consecutive failures
        if webhook.failure_count >= 10:
            webhook.is_active = False
            logger.warning(f"Webhook {webhook.id} auto-deactivated after 10 failures")
    else:
        webhook.failure_count = 0
    
    db.add(delivery)
    await db.flush()
    
    return delivery


async def get_webhook_deliveries(
    db: AsyncSession,
    webhook_id: uuid.UUID,
    page: int = 1,
    page_size: int = 20,
) -> Dict[str, Any]:
    """Get webhook delivery history."""
    query = select(WebhookDelivery).where(WebhookDelivery.webhook_id == webhook_id)
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0
    
    # Paginate
    query = query.order_by(WebhookDelivery.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    deliveries = list(result.scalars().all())
    
    return {
        "items": deliveries,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": (total + page_size - 1) // page_size,
    }
