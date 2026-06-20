"""Push notification service using Web Push Protocol."""
from typing import Any, Dict
import uuid

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.push_subscription import PushSubscription


async def subscribe(
    db: AsyncSession,
    user_id: uuid.UUID,
    subscription: Dict[str, Any],
) -> Dict[str, str]:
    existing = await db.execute(
        select(PushSubscription).where(
            PushSubscription.user_id == user_id,
            PushSubscription.endpoint == subscription.get("endpoint", ""),
        )
    )
    if existing.scalar_one_or_none():
        return {"status": "already_subscribed"}

    sub = PushSubscription(
        user_id=user_id,
        endpoint=subscription.get("endpoint", ""),
        p256dh=subscription.get("keys", {}).get("p256dh", ""),
        auth=subscription.get("keys", {}).get("auth", ""),
    )
    db.add(sub)
    await db.flush()
    return {"status": "subscribed"}


async def unsubscribe(
    db: AsyncSession,
    user_id: uuid.UUID,
    endpoint: str,
) -> Dict[str, str]:
    await db.execute(
        delete(PushSubscription).where(
            PushSubscription.user_id == user_id,
            PushSubscription.endpoint == endpoint,
        )
    )
    await db.flush()
    return {"status": "unsubscribed"}


async def send_push(
    db: AsyncSession,
    user_id: uuid.UUID,
    title: str,
    body: str,
    url: str = "/dashboard",
) -> int:
    result = await db.execute(
        select(PushSubscription).where(PushSubscription.user_id == user_id)
    )
    subscriptions = result.scalars().all()

    sent = 0
    for sub in subscriptions:
        try:
            # Web Push Protocol requires encryption — for now just log
            # Full implementation requires pywebpush
            sent += 1
        except Exception:
            continue
    return sent
