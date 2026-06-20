"""Interview endpoints."""

import asyncio
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings as app_settings
from app.core.database import get_db
from app.core.rate_limit import rate_limit
from app.api.deps import get_current_user
from app.models.user import User
from app.models.question import Question
from app.models.candidate import Candidate
from app.schemas.interview import (
    InterviewCreate,
    InterviewUpdate,
    InterviewResponse,
    InterviewDetailResponse,
    ShareResponse,
    JoinInterviewResponse,
    JoinAnswerRequest,
    JoinAnswerResponse,
)
from app.schemas.common import PaginatedResponse
from app.services import interview_service
from app.services.audit_service import log_action
from app.services.email_service import send_interview_completion_email, send_share_link_email
from app.core.constants import DifficultyLevel

router = APIRouter(prefix="/interviews", tags=["interviews"])


@router.post("", response_model=InterviewResponse, status_code=status.HTTP_201_CREATED, summary="Create an interview", description="Creates a new interview session for a candidate with specified parameters.")
async def create_interview(
    body: InterviewCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    interview = await interview_service.create_interview(db, body, user.id)
    await log_action(db, user.id, "interview.create", "interview", str(interview.id))
    return interview


@router.get("", response_model=PaginatedResponse[InterviewResponse], summary="List interviews", description="Returns a paginated list of interviews with optional status and candidate filters.")
async def list_interviews(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: str | None = Query(None, alias="status"),
    candidate_id: uuid.UUID | None = None,
):
    return await interview_service.list_interviews(db, page, page_size, status_filter, candidate_id)


@router.get("/{interview_id}", response_model=InterviewDetailResponse, summary="Get an interview", description="Returns full details for a specific interview including questions and candidate info.")
async def get_interview(
    interview_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    interview = await interview_service.get_interview(db, interview_id)
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    return interview


@router.patch("/{interview_id}", response_model=InterviewResponse, summary="Update an interview", description="Partially updates an interview's fields such as status or settings.")
async def update_interview(
    interview_id: uuid.UUID,
    body: InterviewUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    interview = await interview_service.update_interview(db, interview_id, body)
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    return interview


@router.post("/{interview_id}/start", response_model=InterviewResponse, summary="Start an interview", description="Transitions an interview from ready to in_progress status and begins the session.")
async def start_interview(
    interview_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    interview = await interview_service.start_interview(db, interview_id)
    if not interview:
        raise HTTPException(status_code=409, detail="Interview cannot be started (wrong status or not found)")
    await log_action(db, user.id, "interview.start", "interview", str(interview_id))
    return interview


@router.post("/{interview_id}/pause", response_model=InterviewResponse, summary="Pause an interview", description="Pauses an active interview to temporarily stop the session.")
async def pause_interview(
    interview_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    interview = await interview_service.pause_interview(db, interview_id)
    if not interview:
        raise HTTPException(status_code=409, detail="Interview cannot be paused")
    return interview


@router.post("/{interview_id}/resume", response_model=InterviewResponse, summary="Resume an interview", description="Resumes a paused interview and continues the session.")
async def resume_interview(
    interview_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    interview = await interview_service.resume_interview(db, interview_id)
    if not interview:
        raise HTTPException(status_code=409, detail="Interview cannot be resumed")
    return interview


@router.post("/{interview_id}/close", response_model=InterviewResponse, summary="Close an interview", description="Marks an interview as completed, calculates the total score, and triggers a completion email.")
async def close_interview(
    interview_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    interview = await interview_service.close_interview(db, interview_id)
    if not interview:
        raise HTTPException(status_code=409, detail="Interview cannot be closed")

    await log_action(db, user.id, "interview.close", "interview", str(interview_id), {"score": interview.total_score})

    result = await db.execute(select(Candidate).where(Candidate.id == interview.candidate_id))
    candidate = result.scalar_one_or_none()
    if candidate and candidate.email:
        asyncio.create_task(
            asyncio.to_thread(
                send_interview_completion_email,
                candidate.email, candidate.name or "", str(interview.id), interview.total_score or 0,
            )
        )

    return interview


@router.delete("/{interview_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete an interview", description="Permanently deletes an interview record from the system.")
async def delete_interview(
    interview_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    success = await interview_service.delete_interview(db, interview_id)
    if not success:
        raise HTTPException(status_code=404, detail="Interview not found")
    await log_action(db, user.id, "interview.delete", "interview", str(interview_id))


@router.post("/{interview_id}/share", response_model=ShareResponse, summary="Share an interview", description="Generates a share token and URL for the interview and sends a share link email to the candidate.")
async def share_interview(
    interview_id: uuid.UUID,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    ip = request.client.host if request.client else "unknown"
    if not rate_limit(f"share:{ip}", 20, 60):
        raise HTTPException(status_code=429, detail="Too many requests")

    if user.role not in ("interviewer", "admin"):
        raise HTTPException(status_code=403, detail="Not allowed")
    interview = await interview_service.get_interview(db, interview_id)
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    if interview.share_token:
        token = interview.share_token
    else:
        token = await interview_service.generate_share_token(interview_id, db)
    share_url = f"{app_settings.CORS_ORIGINS.split(',')[0].strip().rstrip('/')}/dashboard/interview/join/{token}"

    await log_action(db, user.id, "interview.share", "interview", str(interview_id), {"share_token": token})

    result = await db.execute(select(Candidate).where(Candidate.id == interview.candidate_id))
    candidate = result.scalar_one_or_none()
    if candidate and candidate.email:
        asyncio.create_task(
            asyncio.to_thread(
                send_share_link_email,
                candidate.email, candidate.name or "", share_url, user.full_name or "Interviewer",
            )
        )

    return ShareResponse(share_token=token, share_url=share_url)


@router.get("/join/{token}", response_model=JoinInterviewResponse, summary="Join an interview", description="Allows a candidate to join an interview using a share token and returns the first question.")
async def join_interview(
    token: str,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    ip = request.client.host if request.client else "unknown"
    if not rate_limit(f"join:{ip}", 20, 60):
        raise HTTPException(status_code=429, detail="Too many requests")

    interview = await interview_service.get_interview_by_token(token, db)
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    if interview.status not in ("ready", "in_progress"):
        raise HTTPException(status_code=400, detail="Interview is not available")

    cand_result = await db.execute(
        select(Candidate).where(Candidate.id == interview.candidate_id)
    )
    candidate = cand_result.scalar_one_or_none()

    q_result = await db.execute(
        select(func.count()).select_from(Question).where(Question.interview_id == interview.id)
    )
    question_count = q_result.scalar() or 0

    first_q_result = await db.execute(
        select(Question)
        .where(Question.interview_id == interview.id, Question.candidate_answer_text.is_(None))
        .order_by(Question.order_index)
        .limit(1)
    )
    first_question = first_q_result.scalar_one_or_none()
    first_q_dict = None
    if first_question:
        first_q_dict = {
            "id": str(first_question.id),
            "question_text": first_question.question_text,
            "question_type": first_question.question_type,
            "difficulty": first_question.difficulty,
            "order_index": first_question.order_index,
        }

    return JoinInterviewResponse(
        id=str(interview.id),
        candidate_name=candidate.name if candidate else "Unknown",
        question_count=question_count,
        difficulty_level=DifficultyLevel.to_name(interview.difficulty_level),
        status=interview.status,
        first_question=first_q_dict,
    )


@router.post("/join/{token}/answer", response_model=JoinAnswerResponse, summary="Submit a join answer", description="Submits a candidate's answer to a question during a shared interview and returns the next question or completion status.")
async def submit_join_answer(
    token: str,
    body: JoinAnswerRequest,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    ip = request.client.host if request.client else "unknown"
    if not rate_limit(f"join-answer:{ip}", 20, 60):
        raise HTTPException(status_code=429, detail="Too many requests")

    interview = await interview_service.get_interview_by_token(token, db)
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")

    q_result = await db.execute(
        select(Question).where(Question.id == uuid.UUID(body.question_id))
    )
    question = q_result.scalar_one_or_none()
    if not question or question.interview_id != interview.id:
        raise HTTPException(status_code=403, detail="Invalid question")
    if question.candidate_answer_text is not None:
        raise HTTPException(status_code=400, detail="Already answered")

    question.candidate_answer_text = body.answer_text
    score = min(100, len(body.answer_text.split()) * 5)
    question.answer_score = score

    next_q_result = await db.execute(
        select(Question)
        .where(Question.interview_id == interview.id, Question.candidate_answer_text.is_(None))
        .order_by(Question.order_index)
        .limit(1)
    )
    next_question = next_q_result.scalar_one_or_none()

    if next_question:
        return JoinAnswerResponse(
            next_question={
                "id": str(next_question.id),
                "question_text": next_question.question_text,
                "question_type": next_question.question_type,
                "difficulty": next_question.difficulty,
                "order_index": next_question.order_index,
            },
            score=float(score),
            completed=False,
        )
    return JoinAnswerResponse(score=float(score), completed=True)
