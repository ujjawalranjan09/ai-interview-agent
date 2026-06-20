"""Webhook API endpoints."""

import uuid
from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.services import webhook_service
from app.services.audit_service import log_action

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


# Request/Response schemas
class WebhookCreate(BaseModel):
    name: str
    url: str
    events: List[str]
    secret: Optional[str] = None


class WebhookUpdate(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    events: Optional[List[str]] = None
    is_active: Optional[bool] = None
    secret: Optional[str] = None


class WebhookResponse(BaseModel):
    id: str
    name: str
    url: str
    events: List[str]
    is_active: bool
    failure_count: int
    last_triggered_at: Optional[str]
    last_status: Optional[str]
    created_at: str


class DeliveryResponse(BaseModel):
    id: str
    webhook_id: str
    event_type: str
    payload: dict
    response_status: Optional[int]
    response_body: Optional[str]
    success: bool
    error_message: Optional[str]
    attempts: int
    created_at: str


@router.post("", response_model=WebhookResponse, status_code=status.HTTP_201_CREATED)
async def create_webhook(
    body: WebhookCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    """Create a new webhook."""
    webhook = await webhook_service.create_webhook(
        db, body.name, body.url, body.events, user.id, body.secret
    )
    await log_action(db, user.id, "webhook.create", "webhook", str(webhook.id))
    return WebhookResponse(
        id=str(webhook.id),
        name=webhook.name,
        url=webhook.url,
        events=webhook.events or [],
        is_active=webhook.is_active,
        failure_count=webhook.failure_count or 0,
        last_triggered_at=webhook.last_triggered_at,
        last_status=webhook.last_status,
        created_at=webhook.created_at.isoformat() if webhook.created_at else "",
    )


@router.get("")
async def list_webhooks(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """List webhooks for the current user."""
    result = await webhook_service.list_webhooks(db, user.id, page, page_size)
    return {
        "items": [
            WebhookResponse(
                id=str(w.id),
                name=w.name,
                url=w.url,
                events=w.events or [],
                is_active=w.is_active,
                failure_count=w.failure_count or 0,
                last_triggered_at=w.last_triggered_at,
                last_status=w.last_status,
                created_at=w.created_at.isoformat() if w.created_at else "",
            )
            for w in result["items"]
        ],
        "total": result["total"],
        "page": result["page"],
        "page_size": result["page_size"],
        "pages": result["pages"],
    }


@router.get("/{webhook_id}", response_model=WebhookResponse)
async def get_webhook(
    webhook_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    """Get a webhook by ID."""
    webhook = await webhook_service.get_webhook(db, webhook_id)
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")
    return WebhookResponse(
        id=str(webhook.id),
        name=webhook.name,
        url=webhook.url,
        events=webhook.events or [],
        is_active=webhook.is_active,
        failure_count=webhook.failure_count or 0,
        last_triggered_at=webhook.last_triggered_at,
        last_status=webhook.last_status,
        created_at=webhook.created_at.isoformat() if webhook.created_at else "",
    )


@router.patch("/{webhook_id}", response_model=WebhookResponse)
async def update_webhook(
    webhook_id: uuid.UUID,
    body: WebhookUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    """Update a webhook."""
    webhook = await webhook_service.update_webhook(
        db, webhook_id, body.name, body.url, body.events, body.is_active, body.secret
    )
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")
    return WebhookResponse(
        id=str(webhook.id),
        name=webhook.name,
        url=webhook.url,
        events=webhook.events or [],
        is_active=webhook.is_active,
        failure_count=webhook.failure_count or 0,
        last_triggered_at=webhook.last_triggered_at,
        last_status=webhook.last_status,
        created_at=webhook.created_at.isoformat() if webhook.created_at else "",
    )


@router.delete("/{webhook_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_webhook(
    webhook_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    """Delete a webhook."""
    success = await webhook_service.delete_webhook(db, webhook_id)
    if not success:
        raise HTTPException(status_code=404, detail="Webhook not found")
    await log_action(db, user.id, "webhook.delete", "webhook", str(webhook_id))


@router.get("/{webhook_id}/deliveries")
async def get_webhook_deliveries(
    webhook_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """Get webhook delivery history."""
    webhook = await webhook_service.get_webhook(db, webhook_id)
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")
    
    result = await webhook_service.get_webhook_deliveries(db, webhook_id, page, page_size)
    return {
        "items": [
            DeliveryResponse(
                id=str(d.id),
                webhook_id=str(d.webhook_id),
                event_type=d.event_type,
                payload=d.payload,
                response_status=d.response_status,
                response_body=d.response_body,
                success=d.success,
                error_message=d.error_message,
                attempts=d.attempts,
                created_at=d.created_at.isoformat() if d.created_at else "",
            )
            for d in result["items"]
        ],
        "total": result["total"],
        "page": result["page"],
        "page_size": result["page_size"],
        "pages": result["pages"],
    }


@router.post("/{webhook_id}/test")
async def test_webhook(
    webhook_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    """Test a webhook by sending a test event."""
    webhook = await webhook_service.get_webhook(db, webhook_id)
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")
    
    test_payload = {
        "test": True,
        "message": "This is a test webhook delivery",
        "timestamp": int(__import__("time").time()),
    }
    
    delivery = await webhook_service.deliver_webhook(webhook, "test", test_payload, db)
    
    return {
        "delivery_id": str(delivery.id),
        "success": delivery.success,
        "status_code": delivery.response_status,
        "error": delivery.error_message,
    }
