"""Plagiarism detection API endpoints."""
from typing import Optional
import uuid

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.services import plagiarism_service

router = APIRouter(prefix="/plagiarism", tags=["plagiarism"])


@router.post("/checks")
async def create_plagiarism_check(
    body: dict,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await plagiarism_service.create_check(
        db, uuid.UUID(body["submission_id"])
    )


@router.post("/checks/{check_id}/analyze")
async def run_analysis(
    check_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        return await plagiarism_service.run_analysis(db, check_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/checks/{check_id}")
async def get_plagiarism_check(
    check_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check = await plagiarism_service.get_check(db, check_id)
    if not check:
        raise HTTPException(status_code=404, detail="Check not found")
    return check


@router.get("/checks")
async def list_plagiarism_checks(
    submission_id: Optional[uuid.UUID] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await plagiarism_service.list_checks(db, submission_id, page, page_size)
