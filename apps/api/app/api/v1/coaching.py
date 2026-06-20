"""Coaching endpoints."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.candidate import Candidate
from app.models.coaching_plan import CoachingPlan
from app.models.interview import Interview
from app.models.question import Question
from app.models.user import User
from app.schemas.coaching import CoachingPlanResponse

router = APIRouter(tags=["coaching"])


async def _authorize_interview(db: AsyncSession, user: User, interview_id: uuid.UUID) -> Interview:
    result = await db.execute(select(Interview).where(Interview.id == interview_id))
    interview = result.scalar_one_or_none()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    if user.role == "admin":
        return interview
    c_result = await db.execute(select(Candidate).where(Candidate.id == interview.candidate_id))
    candidate = c_result.scalar_one_or_none()
    if candidate and candidate.user_id == user.id:
        return interview
    if interview.interviewer_id and interview.interviewer_id == user.id:
        return interview
    raise HTTPException(status_code=403, detail="Not authorized to access this interview")


@router.get("/interviews/{interview_id}/coaching", response_model=CoachingPlanResponse, summary="Get coaching plan", description="Returns the existing coaching plan with strengths, weaknesses, and study recommendations for an interview.")
async def get_coaching_plan(
    interview_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    await _authorize_interview(db, user, interview_id)
    result = await db.execute(select(CoachingPlan).where(CoachingPlan.interview_id == interview_id))
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Coaching plan not found. POST /coaching/generate to create.")

    return CoachingPlanResponse(
        interview_id=plan.interview_id, candidate_name="", overall_score=plan.overall_score,
        strong_topics=plan.strong_topics or [], weak_topics=plan.weak_topics or [],
        topic_plans=plan.resources or [], one_week_plan=plan.one_week_plan or "",
        one_month_plan=plan.one_month_plan or "", three_month_plan=plan.three_month_plan or "",
        coaching_advice=plan.coaching_advice or "", generated_at=plan.generated_at,
    )


@router.post("/interviews/{interview_id}/coaching/generate", response_model=CoachingPlanResponse, summary="Generate coaching plan", description="Generates or regenerates a personalized coaching plan with a study roadmap based on interview performance.")
async def generate_coaching_plan(
    interview_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    force: bool = Query(False),
):
    interview = await _authorize_interview(db, user, interview_id)
    if interview.status != "completed":
        raise HTTPException(status_code=400, detail="Interview must be completed before generating a coaching plan")

    if not force:
        existing = await db.execute(select(CoachingPlan).where(CoachingPlan.interview_id == interview_id))
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="Coaching plan already exists. Use force=true to regenerate.")

    result = await db.execute(select(Interview).where(Interview.id == interview_id))
    interview = result.scalar_one_or_none()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")

    q_result = await db.execute(select(Question).where(Question.interview_id == interview_id))
    questions = list(q_result.scalars().all())

    c_result = await db.execute(select(Candidate).where(Candidate.id == interview.candidate_id))
    candidate = c_result.scalar_one_or_none()
    candidate_name = candidate.name if candidate else "Candidate"

    q_dicts = [{"question_type": q.question_type, "answer_score": q.answer_score, "target_skill": q.question_type}
               for q in questions]

    from app.services.coaching_service import generate_coaching_plan as gen_plan
    plan_data = gen_plan(candidate_name, q_dicts, interview.total_score)

    # Save or update
    existing = await db.execute(select(CoachingPlan).where(CoachingPlan.interview_id == interview_id))
    plan = existing.scalar_one_or_none()
    if plan:
        plan.overall_score = plan_data["overall_score"]
        plan.strong_topics = plan_data["strong_topics"]
        plan.weak_topics = plan_data["weak_topics"]
        plan.one_week_plan = plan_data["one_week_plan"]
        plan.one_month_plan = plan_data["one_month_plan"]
        plan.three_month_plan = plan_data["three_month_plan"]
        plan.coaching_advice = plan_data["coaching_advice"]
        plan.resources = plan_data["topic_plans"]
    else:
        plan = CoachingPlan(
            interview_id=interview_id, candidate_id=interview.candidate_id,
            overall_score=plan_data["overall_score"], strong_topics=plan_data["strong_topics"],
            weak_topics=plan_data["weak_topics"], one_week_plan=plan_data["one_week_plan"],
            one_month_plan=plan_data["one_month_plan"], three_month_plan=plan_data["three_month_plan"],
            coaching_advice=plan_data["coaching_advice"], resources=plan_data["topic_plans"],
        )
        db.add(plan)

    await db.commit()

    return CoachingPlanResponse(
        interview_id=interview_id, candidate_name=candidate_name,
        overall_score=plan_data["overall_score"], strong_topics=plan_data["strong_topics"],
        weak_topics=plan_data["weak_topics"], topic_plans=plan_data["topic_plans"],
        one_week_plan=plan_data["one_week_plan"], one_month_plan=plan_data["one_month_plan"],
        three_month_plan=plan_data["three_month_plan"], coaching_advice=plan_data["coaching_advice"],
        generated_at=plan.generated_at,
    )
