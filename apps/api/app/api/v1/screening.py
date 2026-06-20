"""AI Screening API endpoints."""
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.schemas.screening import ScreeningRequest, RankRequest
from app.services import screening_service

router = APIRouter(prefix="/screening", tags=["screening"])


@router.post("/candidates/{candidate_id}")
async def screen_candidate(
    candidate_id: uuid.UUID,
    body: ScreeningRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        return await screening_service.screen_candidate(db, candidate_id, body.job_description)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/rank")
async def rank_candidates(
    body: RankRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await screening_service.rank_candidates(db, body.job_description, body.candidate_ids)


@router.get("/candidates/{candidate_id}/history")
async def screening_history(
    candidate_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await screening_service.get_screening_history(db, candidate_id)
