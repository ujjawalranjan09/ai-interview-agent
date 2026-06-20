"""Candidate endpoints."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.candidate import CandidateCreate, CandidateUpdate, CandidateResponse, CandidateDetailResponse
from app.schemas.common import PaginatedResponse
from app.services import candidate_service

router = APIRouter(prefix="/candidates", tags=["candidates"])


@router.post("", response_model=CandidateResponse, status_code=status.HTTP_201_CREATED, summary="Create a candidate", description="Creates a new candidate record with the provided details.")
async def create_candidate(
    body: CandidateCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    candidate = await candidate_service.create_candidate(db, body)
    return candidate


@router.get("", response_model=PaginatedResponse[CandidateResponse], summary="List candidates", description="Returns a paginated list of candidates with optional search filtering.")
async def list_candidates(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = None,
):
    return await candidate_service.list_candidates(db, page, page_size, search)


@router.get("/{candidate_id}", response_model=CandidateDetailResponse, summary="Get a candidate", description="Returns detailed information for a specific candidate by ID.")
async def get_candidate(
    candidate_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    candidate = await candidate_service.get_candidate(db, candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return candidate


@router.put("/{candidate_id}", response_model=CandidateResponse, summary="Update a candidate", description="Updates an existing candidate's information.")
async def update_candidate(
    candidate_id: uuid.UUID,
    body: CandidateUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    candidate = await candidate_service.update_candidate(db, candidate_id, body)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return candidate


@router.post("/{candidate_id}/upload-resume", response_model=CandidateDetailResponse, summary="Upload candidate resume", description="Uploads a PDF resume for a candidate and extracts skills from it.")
async def upload_resume(
    candidate_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    file: UploadFile = File(...),
):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    file_bytes = await file.read()
    candidate = await candidate_service.upload_resume(db, candidate_id, file_bytes, file.filename)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return candidate
