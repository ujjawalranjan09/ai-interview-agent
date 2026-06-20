import uuid
from datetime import datetime, timedelta, timezone
from typing import Annotated
from collections import Counter

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.cache import cache_get, cache_set
from app.api.deps import get_current_user
from app.models.user import User
from app.models.interview import Interview
from app.models.candidate import Candidate
from app.schemas.analytics import (
    OverviewResponse,
    CandidateHistoryItem,
    CandidateHistoryResponse,
    TrendResponse,
)

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/overview", response_model=OverviewResponse, summary="Get analytics overview", description="Returns aggregate metrics including total interviews, average score, top skills, and weekly activity.")
async def get_overview(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    if user.role not in ("admin", "interviewer"):
        raise HTTPException(status_code=403, detail="Not allowed")

    cache_key = f"overview:{user.id}"
    cached = await cache_get(cache_key)
    if cached:
        return OverviewResponse(**cached)

    total = await db.execute(select(func.count()).select_from(Interview))
    total_interviews = total.scalar() or 0

    completed = await db.execute(
        select(func.count()).select_from(Interview).where(Interview.status == "completed")
    )
    completed_interviews = completed.scalar() or 0

    avg = await db.execute(
        select(func.avg(Interview.total_score))
        .where(Interview.status == "completed", Interview.total_score.isnot(None))
    )
    average_score = round(avg.scalar() or 0, 1)

    cand_total = await db.execute(select(func.count()).select_from(Candidate))
    total_candidates = cand_total.scalar() or 0

    week_ago = datetime.now(timezone.utc) - timedelta(days=7)
    week_q = await db.execute(
        select(func.count()).select_from(Interview).where(Interview.created_at >= week_ago)
    )
    interviews_this_week = week_q.scalar() or 0

    skills_result = await db.execute(
        select(Candidate.extracted_skills).where(Candidate.extracted_skills.isnot(None))
    )
    all_skills = []
    for row in skills_result.scalars().all():
        if isinstance(row, list):
            all_skills.extend(row)
    top_skills = [
        {"skill": k, "count": v}
        for k, v in Counter(all_skills).most_common(10)
    ]

    result = OverviewResponse(
        total_interviews=total_interviews,
        completed_interviews=completed_interviews,
        average_score=average_score,
        total_candidates=total_candidates,
        interviews_this_week=interviews_this_week,
        top_skills=top_skills,
    )
    await cache_set(cache_key, result.model_dump(), ttl=60)
    return result


@router.get("/candidates/{candidate_id}/history", response_model=CandidateHistoryResponse, summary="Get candidate history", description="Returns the interview history and performance timeline for a specific candidate.")
async def get_candidate_history(
    candidate_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    cand_result = await db.execute(
        select(Candidate).where(Candidate.id == candidate_id)
    )
    candidate = cand_result.scalar_one_or_none()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    if user.role not in ("admin", "interviewer") and candidate.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not allowed")

    iv_result = await db.execute(
        select(Interview)
        .where(Interview.candidate_id == candidate_id)
        .order_by(Interview.created_at.desc())
        .limit(50)
    )
    interviews = iv_result.scalars().all()

    items = [
        CandidateHistoryItem(
            interview_id=str(iv.id),
            date=iv.created_at.isoformat() if iv.created_at else "",
            score=iv.total_score or 0,
            status=iv.status,
            question_count=iv.question_count,
        )
        for iv in interviews
    ]
    return CandidateHistoryResponse(items=items)


@router.get("/trends", response_model=TrendResponse, summary="Get analytics trends", description="Returns weekly score trends and skill distribution across all completed interviews.")
async def get_trends(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    if user.role not in ("admin", "interviewer"):
        raise HTTPException(status_code=403, detail="Not allowed")

    cache_key = f"trends:{user.id}"
    cached = await cache_get(cache_key)
    if cached:
        return TrendResponse(**cached)

    weekly_scores = []
    try:
        weekly_result = await db.execute(
            select(
                func.date_trunc("week", Interview.created_at).label("week_start"),
                func.avg(Interview.total_score).label("average_score"),
                func.count().label("interview_count"),
            )
            .where(
                Interview.status == "completed",
                Interview.total_score.isnot(None),
                Interview.created_at >= func.now() - func.make_interval(0, 0, 0, 84),
            )
            .group_by(text("week_start"))
            .order_by(text("week_start"))
        )
        weekly_scores = [
            {
                "week_start": str(row.week_start),
                "average_score": round(float(row.average_score), 1) if row.average_score else 0,
                "interview_count": row.interview_count,
            }
            for row in weekly_result.fetchall()
        ]
    except Exception:
        weekly_scores = []

    skills_result = await db.execute(
        select(Candidate.extracted_skills).where(Candidate.extracted_skills.isnot(None))
    )
    all_skills = []
    for row in skills_result.scalars().all():
        if isinstance(row, list):
            all_skills.extend(row)
    skill_distribution = [
        {"skill": k, "count": v}
        for k, v in Counter(all_skills).most_common(15)
    ]

    result = TrendResponse(
        weekly_scores=weekly_scores,
        skill_distribution=skill_distribution,
    )
    await cache_set(cache_key, result.model_dump(), ttl=60)
    return result
