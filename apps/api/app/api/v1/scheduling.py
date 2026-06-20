"""Scheduling API endpoints."""
from datetime import datetime
from typing import Optional
import uuid

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.services import scheduling_service

router = APIRouter(prefix="/scheduling", tags=["scheduling"])


@router.get("/availability")
async def get_availability(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await scheduling_service.get_availability(db, user.id)


@router.put("/availability")
async def set_availability(
    body: dict,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await scheduling_service.set_availability(db, user.id, body["slots"])


@router.post("/schedule")
async def schedule_interview(
    body: dict,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await scheduling_service.schedule_interview(
        db,
        uuid.UUID(body["interview_id"]),
        uuid.UUID(body["candidate_id"]),
        datetime.fromisoformat(body["scheduled_at"]),
        body.get("duration_minutes", 60),
        interviewer_id=user.id,
        notes=body.get("notes"),
    )


@router.get("/scheduled")
async def list_scheduled(
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await scheduling_service.get_scheduled_interviews(
        db, interviewer_id=user.id, status=status, page=page, page_size=page_size
    )


@router.put("/scheduled/{scheduled_id}")
async def reschedule(
    scheduled_id: uuid.UUID,
    body: dict,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        return await scheduling_service.reschedule_interview(
            db,
            scheduled_id,
            datetime.fromisoformat(body["scheduled_at"]),
            notes=body.get("notes"),
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/scheduled/{scheduled_id}")
async def cancel_scheduled(
    scheduled_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        return await scheduling_service.cancel_scheduled_interview(db, scheduled_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
