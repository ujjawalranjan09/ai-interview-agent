import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.interview import Interview
from app.models.question import Question
from app.models.candidate import Candidate
from app.models.copilot_session import CopilotSession
from app.schemas.copilot import (
    CopilotSessionResponse,
    SuggestionsResponse,
    SuggestionResponse,
)
from app.services import copilot_service
from app.services.audit_service import log_action

router = APIRouter(prefix="/interviews/{interview_id}/copilot", tags=["copilot"])


def _check_role(user: User):
    if user.role not in ("interviewer", "admin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")


@router.post("/start", response_model=CopilotSessionResponse, summary="Start copilot session", description="Creates or retrieves an AI copilot session for an interview to provide real-time suggestions.")
async def start_copilot(
    interview_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    _check_role(user)
    interview = await db.execute(select(Interview).where(Interview.id == interview_id))
    if not interview.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Interview not found")
    session = await copilot_service.get_or_create_session(interview_id, user.id, db)
    await log_action(db, user.id, "copilot.start", "copilot_session", str(session.id), {"interview_id": str(interview_id)})
    return CopilotSessionResponse(
        id=str(session.id),
        interview_id=str(session.interview_id),
        interviewer_id=str(session.interviewer_id),
        created_at=session.created_at.isoformat() if session.created_at else "",
    )


@router.get("/suggestions", response_model=SuggestionsResponse, summary="Get copilot suggestions", description="Generates and returns AI-powered suggestions based on the latest question and candidate response.")
async def get_suggestions(
    interview_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    _check_role(user)
    result = await db.execute(select(Interview).where(Interview.id == interview_id))
    interview = result.scalar_one_or_none()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")

    q_result = await db.execute(
        select(Question)
        .where(Question.interview_id == interview_id)
        .order_by(Question.order_index.desc())
        .limit(1)
    )
    question = q_result.scalar_one_or_none()

    cand_result = await db.execute(
        select(Candidate).where(Candidate.id == interview.candidate_id)
    )
    candidate = cand_result.scalar_one_or_none()

    suggestions = await copilot_service.generate_suggestions(
        interview_id,
        question.question_text if question else "",
        question.candidate_answer_text if question and question.candidate_answer_text else "",
        question.answer_score if question and question.answer_score else 0,
        candidate.extracted_skills if candidate and candidate.extracted_skills else [],
        db,
    )
    return SuggestionsResponse(
        suggestions=[SuggestionResponse(**s) for s in suggestions]
    )


@router.post("/dismiss/{suggestion_id}", summary="Dismiss a suggestion", description="Marks a copilot suggestion as dismissed by the interviewer.")
async def dismiss_suggestion(
    interview_id: uuid.UUID,
    suggestion_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    _check_role(user)
    result = await db.execute(
        select(CopilotSession).where(CopilotSession.interview_id == interview_id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Copilot session not found")
    if session.suggestions_log:
        for s in session.suggestions_log:
            if s.get("id") == suggestion_id:
                s["dismissed"] = True
                break
    await db.commit()
    return {"status": "dismissed"}
