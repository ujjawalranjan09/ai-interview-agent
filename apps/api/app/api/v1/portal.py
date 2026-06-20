"""Candidate Portal API endpoints."""

import uuid
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.services import candidate_portal
from app.services.audit_service import log_action

router = APIRouter(prefix="/portal", tags=["candidate-portal"])


# Request/Response schemas
class ProfileUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None


class ProfileResponse(BaseModel):
    id: str
    name: str
    email: str | None
    phone: str | None
    skills: list[str]
    stats: dict
    created_at: str


class InterviewResponse(BaseModel):
    id: str
    status: str
    total_score: float | None
    questions_answered: int
    question_count: int
    start_time: str | None
    end_time: str | None
    created_at: str


class InterviewReportResponse(BaseModel):
    interview_id: str
    status: str
    total_score: float | None
    questions_answered: int
    question_count: int
    start_time: str | None
    end_time: str | None
    questions: list[dict]
    created_at: str


@router.get("/profile", response_model=ProfileResponse)
async def get_profile(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    """Get candidate profile."""
    # For demo, use user ID as candidate ID
    candidate_id = user.id
    
    profile = await candidate_portal.get_candidate_profile(db, candidate_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Candidate not found")
    
    return ProfileResponse(
        id=profile["id"],
        name=profile["name"],
        email=profile["email"],
        phone=profile["phone"],
        skills=profile["skills"],
        stats=profile["stats"],
        created_at=profile["created_at"],
    )


@router.patch("/profile", response_model=ProfileResponse)
async def update_profile(
    body: ProfileUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    """Update candidate profile."""
    candidate_id = user.id
    
    candidate = await candidate_portal.update_candidate_profile(
        db, candidate_id, body.name, body.email, body.phone
    )
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    
    await log_action(db, user.id, "portal.profile.update", "candidate", str(candidate_id))
    
    # Get updated profile
    profile = await candidate_portal.get_candidate_profile(db, candidate_id)
    return ProfileResponse(
        id=profile["id"],
        name=profile["name"],
        email=profile["email"],
        phone=profile["phone"],
        skills=profile["skills"],
        stats=profile["stats"],
        created_at=profile["created_at"],
    )


@router.get("/interviews")
async def get_interviews(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """Get candidate's interview history."""
    candidate_id = user.id
    
    result = await candidate_portal.get_candidate_interviews(db, candidate_id, page, page_size)
    return {
        "items": [
            InterviewResponse(
                id=str(i.id),
                status=i.status,
                total_score=i.total_score,
                questions_answered=i.questions_answered,
                question_count=i.question_count,
                start_time=i.start_time.isoformat() if i.start_time else None,
                end_time=i.end_time.isoformat() if i.end_time else None,
                created_at=i.created_at.isoformat() if i.created_at else "",
            )
            for i in result["items"]
        ],
        "total": result["total"],
        "page": result["page"],
        "page_size": result["page_size"],
        "pages": result["pages"],
    }


@router.get("/interviews/{interview_id}/report", response_model=InterviewReportResponse)
async def get_interview_report(
    interview_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    """Get detailed interview report."""
    candidate_id = user.id
    
    report = await candidate_portal.get_interview_report(db, interview_id, candidate_id)
    if not report:
        raise HTTPException(status_code=404, detail="Interview not found")
    
    return InterviewReportResponse(**report)
