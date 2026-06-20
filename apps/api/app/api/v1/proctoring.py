"""Proctoring API endpoints."""
from typing import Optional
import uuid

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.services import proctoring_service

router = APIRouter(prefix="/proctoring", tags=["proctoring"])


@router.post("/sessions")
async def create_session(
    body: dict,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await proctoring_service.start_session(
        db,
        uuid.UUID(body["interview_id"]),
        config=body.get("config"),
    )


@router.post("/sessions/{session_id}/end")
async def end_proctoring_session(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        return await proctoring_service.end_session(db, session_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/sessions/{session_id}/events")
async def log_proctoring_event(
    session_id: uuid.UUID,
    body: dict,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await proctoring_service.log_event(
        db,
        session_id,
        body["event_type"],
        body.get("severity", "info"),
        body.get("confidence", 0.0),
        body.get("details"),
    )


@router.get("/sessions/{session_id}")
async def get_proctoring_session(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    session = await proctoring_service.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.get("/sessions")
async def list_proctoring_sessions(
    interview_id: Optional[uuid.UUID] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await proctoring_service.list_sessions(db, interview_id, page, page_size)
