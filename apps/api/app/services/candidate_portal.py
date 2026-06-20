"""Candidate Portal service — candidate-facing features."""

import uuid
from typing import Any, Dict, Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.candidate import Candidate
from app.models.interview import Interview
from app.models.question import Question


async def get_candidate_profile(
    db: AsyncSession,
    candidate_id: uuid.UUID,
) -> Optional[Dict[str, Any]]:
    """Get candidate profile with interview history."""
    result = await db.execute(select(Candidate).where(Candidate.id == candidate_id))
    candidate = result.scalar_one_or_none()
    
    if not candidate:
        return None
    
    # Get interview history
    interview_result = await db.execute(
        select(Interview)
        .where(Interview.candidate_id == candidate_id)
        .order_by(Interview.created_at.desc())
    )
    interviews = list(interview_result.scalars().all())
    
    # Calculate statistics
    completed_interviews = [i for i in interviews if i.status == "completed"]
    total_score = sum(i.total_score or 0 for i in completed_interviews)
    avg_score = total_score / len(completed_interviews) if completed_interviews else 0
    
    return {
        "id": str(candidate.id),
        "name": candidate.name,
        "email": candidate.email,
        "phone": candidate.phone,
        "skills": candidate.extracted_skills or [],
        "resume_text": candidate.resume_text,
        "stats": {
            "total_interviews": len(interviews),
            "completed_interviews": len(completed_interviews),
            "average_score": round(avg_score, 1),
            "best_score": round(max((i.total_score or 0) for i in completed_interviews), 1) if completed_interviews else 0,
        },
        "created_at": candidate.created_at.isoformat() if candidate.created_at else "",
    }


async def get_candidate_interviews(
    db: AsyncSession,
    candidate_id: uuid.UUID,
    page: int = 1,
    page_size: int = 20,
) -> Dict[str, Any]:
    """Get candidate's interview history."""
    query = select(Interview).where(Interview.candidate_id == candidate_id)
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0
    
    # Paginate
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    interviews = list(result.scalars().all())
    
    return {
        "items": interviews,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": (total + page_size - 1) // page_size,
    }


async def get_interview_report(
    db: AsyncSession,
    interview_id: uuid.UUID,
    candidate_id: uuid.UUID,
) -> Optional[Dict[str, Any]]:
    """Get detailed interview report for candidate."""
    result = await db.execute(
        select(Interview)
        .where(Interview.id == interview_id, Interview.candidate_id == candidate_id)
    )
    interview = result.scalar_one_or_none()
    
    if not interview:
        return None
    
    # Get questions with answers
    q_result = await db.execute(
        select(Question)
        .where(Question.interview_id == interview_id)
        .order_by(Question.order_index)
    )
    questions = list(q_result.scalars().all())
    
    question_details = []
    for q in questions:
        question_details.append({
            "id": str(q.id),
            "question_text": q.question_text,
            "question_type": q.question_type,
            "difficulty": q.difficulty,
            "order_index": q.order_index,
            "answer": q.candidate_answer_text,
            "score": q.answer_score,
            "semantic_score": q.semantic_score,
            "keyword_score": q.keyword_score,
            "concept_score": q.concept_score,
        })
    
    return {
        "interview_id": str(interview.id),
        "status": interview.status,
        "total_score": interview.total_score,
        "questions_answered": interview.questions_answered,
        "question_count": interview.question_count,
        "start_time": interview.start_time.isoformat() if interview.start_time else None,
        "end_time": interview.end_time.isoformat() if interview.end_time else None,
        "questions": question_details,
        "created_at": interview.created_at.isoformat() if interview.created_at else "",
    }


async def update_candidate_profile(
    db: AsyncSession,
    candidate_id: uuid.UUID,
    name: Optional[str] = None,
    email: Optional[str] = None,
    phone: Optional[str] = None,
) -> Optional[Candidate]:
    """Update candidate profile."""
    result = await db.execute(select(Candidate).where(Candidate.id == candidate_id))
    candidate = result.scalar_one_or_none()
    
    if not candidate:
        return None
    
    if name is not None:
        candidate.name = name
    if email is not None:
        candidate.email = email
    if phone is not None:
        candidate.phone = phone
    
    await db.flush()
    return candidate
