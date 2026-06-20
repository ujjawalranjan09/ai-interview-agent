"""Search service — full-text search across platform entities."""

from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.candidate import Candidate
from app.models.interview import Interview
from app.models.question import Question
from app.models.question_bank import QuestionBank
from app.models.user import User


async def search_all(
    query: str,
    user: User,
    db: AsyncSession,
    search_type: Optional[str] = None,
) -> Dict[str, Any]:
    """Search across all entity types or filter by type."""
    results = {}
    total = 0

    if not search_type or search_type == "candidates":
        results["candidates"] = await search_candidates(query, db)
        total += len(results["candidates"])

    if not search_type or search_type == "interviews":
        results["interviews"] = await search_interviews(query, db)
        total += len(results["interviews"])

    if not search_type or search_type == "questions":
        results["questions"] = await search_questions(query, db)
        total += len(results["questions"])

    if not search_type or search_type == "banks":
        results["banks"] = await search_banks(query, db)
        total += len(results["banks"])

    results["total"] = total
    return results


async def search_candidates(
    query: str,
    db: AsyncSession,
) -> List[Dict[str, Any]]:
    like_pattern = f"%{query}%"
    stmt = select(Candidate).where(
        Candidate.name.ilike(like_pattern)
        | Candidate.email.ilike(like_pattern)
    )
    stmt = stmt.limit(20)

    result = await db.execute(stmt)
    candidates = list(result.scalars().all())

    return [
        {
            "id": str(c.id),
            "type": "candidate",
            "title": c.name,
            "subtitle": c.email or "",
            "link": f"/dashboard/candidates/{c.id}",
        }
        for c in candidates
    ]


async def search_interviews(
    query: str,
    db: AsyncSession,
) -> List[Dict[str, Any]]:
    like_pattern = f"%{query}%"
    stmt = (
        select(Interview)
        .join(Candidate, Interview.candidate_id == Candidate.id, isouter=True)
        .where(Candidate.name.ilike(like_pattern))
    )
    stmt = stmt.limit(20)

    result = await db.execute(stmt)
    interviews = list(result.scalars().all())

    return [
        {
            "id": str(i.id),
            "type": "interview",
            "title": f"Interview {str(i.id)[:8]}...",
            "subtitle": i.status,
            "link": f"/dashboard/interviews/{i.id}",
        }
        for i in interviews
    ]


async def search_questions(
    query: str,
    db: AsyncSession,
) -> List[Dict[str, Any]]:
    like_pattern = f"%{query}%"
    stmt = select(Question).where(Question.question_text.ilike(like_pattern))
    stmt = stmt.limit(20)

    result = await db.execute(stmt)
    questions = list(result.scalars().all())

    return [
        {
            "id": str(q.id),
            "type": "question",
            "title": q.question_text[:100],
            "subtitle": q.question_type,
            "link": f"/dashboard/questions/{q.id}",
        }
        for q in questions
    ]


async def search_banks(
    query: str,
    db: AsyncSession,
) -> List[Dict[str, Any]]:
    like_pattern = f"%{query}%"
    stmt = select(QuestionBank).where(
        QuestionBank.name.ilike(like_pattern)
        | (QuestionBank.description.ilike(like_pattern))
    )
    stmt = stmt.limit(20)

    result = await db.execute(stmt)
    banks = list(result.scalars().all())

    return [
        {
            "id": str(b.id),
            "type": "bank",
            "title": b.name,
            "subtitle": b.category,
            "link": f"/dashboard/banks/{b.id}",
        }
        for b in banks
    ]
