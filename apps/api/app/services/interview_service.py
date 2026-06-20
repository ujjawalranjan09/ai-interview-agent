"""Interview service — CRUD + lifecycle management."""

import secrets
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.interview import Interview
from app.models.candidate import Candidate
from app.schemas.interview import InterviewCreate, InterviewUpdate
from app.services.screening_service import screen_candidate


async def create_interview(db: AsyncSession, data: InterviewCreate, interviewer_id: uuid.UUID | None = None) -> Interview:
    interview = Interview(
        candidate_id=data.candidate_id,
        interviewer_id=interviewer_id,
        difficulty_level=data.difficulty_level,
        question_count=data.question_count,
        config=data.config,
        status="draft",
    )
    db.add(interview)
    await db.flush()
    return interview


async def get_interview(db: AsyncSession, interview_id: uuid.UUID) -> Interview | None:
    result = await db.execute(select(Interview).where(Interview.id == interview_id))
    return result.scalar_one_or_none()


async def list_interviews(
    db: AsyncSession, page: int = 1, page_size: int = 20,
    status: str | None = None, candidate_id: uuid.UUID | None = None,
) -> dict:
    query = select(Interview)
    count_query = select(func.count()).select_from(Interview)

    if status:
        query = query.where(Interview.status == status)
        count_query = count_query.where(Interview.status == status)
    if candidate_id:
        query = query.where(Interview.candidate_id == candidate_id)
        count_query = count_query.where(Interview.candidate_id == candidate_id)

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = query.order_by(Interview.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    items = list(result.scalars().all())

    return {"items": items, "total": total, "page": page, "page_size": page_size}


async def update_interview(db: AsyncSession, interview_id: uuid.UUID, data: InterviewUpdate) -> Interview | None:
    interview = await get_interview(db, interview_id)
    if not interview:
        return None
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(interview, key, value)
    await db.flush()
    return interview


async def start_interview(db: AsyncSession, interview_id: uuid.UUID) -> Interview | None:
    interview = await get_interview(db, interview_id)
    if not interview or interview.status != "draft":
        return None

    # Get candidate skills
    result = await db.execute(select(Candidate).where(Candidate.id == interview.candidate_id))
    candidate = result.scalar_one_or_none()
    skills = candidate.extracted_skills if candidate and candidate.extracted_skills else ["python", "javascript", "sql"]
    projects = candidate.extracted_projects if candidate and candidate.extracted_projects else []

    from app.ml.questions.difficulty_manager import DifficultyManager
    dm = DifficultyManager(interview.difficulty_level)
    difficulty_name = dm.difficulty_name

    from app.services.question_service import generate_interview_questions
    await generate_interview_questions(
        db=db,
        interview_id=interview_id,
        skills=skills,
        projects=projects,
        count=interview.question_count,
        difficulty=difficulty_name,
    )

    interview.status = "in_progress"
    interview.start_time = datetime.now(timezone.utc)
    await db.flush()
    return interview


async def pause_interview(db: AsyncSession, interview_id: uuid.UUID) -> Interview | None:
    interview = await get_interview(db, interview_id)
    if not interview or interview.status != "in_progress":
        return None
    interview.status = "paused"
    await db.flush()
    return interview


async def resume_interview(db: AsyncSession, interview_id: uuid.UUID) -> Interview | None:
    interview = await get_interview(db, interview_id)
    if not interview or interview.status != "paused":
        return None
    interview.status = "in_progress"
    await db.flush()
    return interview


async def close_interview(db: AsyncSession, interview_id: uuid.UUID) -> Interview | None:
    interview = await get_interview(db, interview_id)
    if not interview or interview.status not in ("in_progress", "paused"):
        return None

    # Calculate total_score from answered questions
    from app.models.question import Question
    result = await db.execute(
        select(Question)
        .where(Question.interview_id == interview_id, Question.answer_score > 0)
    )
    questions = list(result.scalars().all())
    if questions:
        interview.total_score = round(sum(q.answer_score for q in questions) / len(questions), 1)
        interview.questions_answered = len(questions)

    interview.status = "completed"
    interview.end_time = datetime.now(timezone.utc)
    await db.flush()
    return interview


async def generate_share_token(interview_id: uuid.UUID, db: AsyncSession) -> str:
    result = await db.execute(select(Interview).where(Interview.id == interview_id))
    interview = result.scalar_one_or_none()
    if not interview:
        return ""
    token = secrets.token_urlsafe(32)
    interview.share_token = token
    await db.flush()
    return token


async def get_interview_by_token(token: str, db: AsyncSession) -> Interview | None:
    result = await db.execute(select(Interview).where(Interview.share_token == token))
    return result.scalar_one_or_none()


async def delete_interview(db: AsyncSession, interview_id: uuid.UUID) -> bool:
    interview = await get_interview(db, interview_id)
    if not interview:
        return False
    interview.status = "cancelled"
    await db.flush()
    return True


async def auto_screen_for_interview(
    db: AsyncSession,
    interview_id: uuid.UUID,
    candidate_id: uuid.UUID,
    job_description: str,
) -> Optional[Dict[str, Any]]:
    try:
        result = await screen_candidate(db, candidate_id, job_description)
        interview_result = await db.execute(
            select(Interview).where(Interview.id == interview_id)
        )
        interview = interview_result.scalar_one_or_none()
        if interview:
            if not interview.config:
                interview.config = {}
            interview.config["screening_result"] = result
            await db.flush()
        return result
    except Exception:
        return None
