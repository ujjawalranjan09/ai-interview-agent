"""Plagiarism detection service — code similarity analysis."""

import uuid
from typing import Any, Dict, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.plagiarism import PlagiarismCheck, PlagiarismMatch
from app.models.coding_question import CodingSubmission


async def create_check(
    db: AsyncSession,
    submission_id: uuid.UUID,
) -> Dict[str, Any]:
    check = PlagiarismCheck(submission_id=submission_id, status="pending")
    db.add(check)
    await db.flush()
    return {"id": str(check.id), "status": "pending"}


async def run_analysis(
    db: AsyncSession,
    check_id: uuid.UUID,
) -> Dict[str, Any]:
    result = await db.execute(
        select(PlagiarismCheck).where(PlagiarismCheck.id == check_id)
    )
    check = result.scalar_one_or_none()
    if not check:
        raise ValueError("Plagiarism check not found")

    sub_result = await db.execute(
        select(CodingSubmission).where(CodingSubmission.id == check.submission_id)
    )
    submission = sub_result.scalar_one_or_none()
    if not submission:
        check.status = "failed"
        await db.flush()
        raise ValueError("Submission not found")

    other_result = await db.execute(
        select(CodingSubmission).where(
            CodingSubmission.id != check.submission_id,
            CodingSubmission.language == submission.language,
        )
    )
    other_submissions = list(other_result.scalars().all())

    matches = []
    max_similarity = 0.0
    matched_id = None

    for other in other_submissions:
        similarity = _compute_similarity(submission.code or "", other.code or "")
        if similarity > 0.5:
            match = PlagiarismMatch(
                check_id=check_id,
                matched_submission_id=other.id,
                similarity=similarity,
                algorithm="moss",
            )
            db.add(match)
            matches.append(match)
            if similarity > max_similarity:
                max_similarity = similarity
                matched_id = other.id

    check.status = "completed"
    check.similarity_score = max_similarity
    check.matched_with = matched_id
    check.matched_source = "repository"
    check.details = {"matches_count": len(matches)}
    await db.flush()

    return {
        "id": str(check.id),
        "status": "completed",
        "similarity_score": max_similarity,
        "matches_count": len(matches),
    }


def _compute_similarity(code_a: str, code_b: str) -> float:
    if not code_a or not code_b:
        return 0.0
    tokens_a = set(code_a.split())
    tokens_b = set(code_b.split())
    if not tokens_a or not tokens_b:
        return 0.0
    intersection = tokens_a & tokens_b
    union = tokens_a | tokens_b
    return len(intersection) / len(union)


async def get_check(
    db: AsyncSession, check_id: uuid.UUID
) -> Optional[Dict[str, Any]]:
    result = await db.execute(
        select(PlagiarismCheck).where(PlagiarismCheck.id == check_id)
    )
    check = result.scalar_one_or_none()
    if not check:
        return None

    matches_result = await db.execute(
        select(PlagiarismMatch).where(PlagiarismMatch.check_id == check_id)
    )
    matches = matches_result.scalars().all()

    return {
        "id": str(check.id),
        "submission_id": str(check.submission_id),
        "status": check.status,
        "similarity_score": check.similarity_score,
        "matched_with": str(check.matched_with) if check.matched_with else None,
        "matched_source": check.matched_source,
        "matches": [
            {
                "id": str(m.id),
                "matched_submission_id": str(m.matched_submission_id),
                "similarity": m.similarity,
                "algorithm": m.algorithm,
            }
            for m in matches
        ],
    }


async def list_checks(
    db: AsyncSession,
    submission_id: Optional[uuid.UUID] = None,
    page: int = 1,
    page_size: int = 20,
) -> Dict[str, Any]:
    stmt = select(PlagiarismCheck)
    if submission_id:
        stmt = stmt.where(PlagiarismCheck.submission_id == submission_id)
    stmt = stmt.order_by(PlagiarismCheck.created_at.desc())
    stmt = stmt.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(stmt)
    checks = result.scalars().all()

    return {
        "items": [
            {
                "id": str(c.id),
                "submission_id": str(c.submission_id),
                "status": c.status,
                "similarity_score": c.similarity_score,
            }
            for c in checks
        ],
        "total": len(checks),
        "page": page,
        "page_size": page_size,
    }
