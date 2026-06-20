import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.candidate import Candidate
from app.schemas.jd import JDUploadRequest, JDMatchResponse, JDQuestionRequest, JDQuestionResponse, JDQuestionItem
from app.services import jd_service
from app.services.audit_service import log_action

router = APIRouter(prefix="/candidates/{candidate_id}/jd", tags=["jd-matching"])


async def _load_candidate(candidate_id: uuid.UUID, db: AsyncSession, user: User) -> Candidate:
    result = await db.execute(select(Candidate).where(Candidate.id == candidate_id))
    candidate = result.scalar_one_or_none()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    if user.role not in ("admin", "interviewer") and candidate.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not allowed")
    return candidate


@router.post("", response_model=JDMatchResponse, summary="Match job description", description="Analyzes a job description against a candidate's skills and returns a match score with gap analysis.")
async def match_jd(
    candidate_id: uuid.UUID,
    body: JDUploadRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    candidate = await _load_candidate(candidate_id, db, user)
    extracted = jd_service.extract_skills_from_jd(body.jd_text)
    result = jd_service.calculate_match(candidate.extracted_skills or [], extracted)
    await log_action(db, user.id, "jd.match", "candidate", str(candidate_id))
    return result


@router.post("/questions", response_model=JDQuestionResponse, summary="Generate JD questions", description="Generates interview questions targeting skill gaps identified from a job description match.")
async def generate_jd_questions(
    candidate_id: uuid.UUID,
    body: JDQuestionRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    candidate = await _load_candidate(candidate_id, db, user)
    extracted = jd_service.extract_skills_from_jd(body.jd_text)
    match_result = jd_service.calculate_match(candidate.extracted_skills or [], extracted)
    questions = jd_service.generate_jd_questions(match_result["missing_required"], body.count)
    await log_action(db, user.id, "jd.generate_questions", "candidate", str(candidate_id))
    return JDQuestionResponse(questions=[JDQuestionItem(**q) for q in questions])
