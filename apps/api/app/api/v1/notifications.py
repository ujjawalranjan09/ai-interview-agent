"""Push notification API endpoints."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.services import push_service

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.post("/subscribe")
async def subscribe(
    body: dict,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await push_service.subscribe(db, user.id, body.get("subscription", {}))


@router.post("/unsubscribe")
async def unsubscribe(
    body: dict,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await push_service.unsubscribe(db, user.id, body.get("endpoint", ""))


@router.post("/test")
async def test_notification(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    count = await push_service.send_push(db, user.id, "Test Notification", "This is a test notification")
    return {"sent": count}
