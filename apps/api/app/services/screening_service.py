"""AI screening service — resume vs job description analysis."""

import hashlib
import uuid
from typing import Any, Dict, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.candidate import Candidate
from app.models.screening_result import ScreeningResult


async def screen_candidate(
    db: AsyncSession,
    candidate_id: uuid.UUID,
    job_description: str,
) -> Dict[str, Any]:
    jd_hash = hashlib.sha256(job_description.encode()).hexdigest()[:64]

    existing = await db.execute(
        select(ScreeningResult).where(
            ScreeningResult.candidate_id == candidate_id,
            ScreeningResult.job_description_hash == jd_hash,
        )
    )
    existing_result = existing.scalar_one_or_none()
    if existing_result:
        return _format_result(existing_result)

    result = await db.execute(
        select(Candidate).where(Candidate.id == candidate_id)
    )
    candidate = result.scalar_one_or_none()
    if not candidate:
        raise ValueError("Candidate not found")

    required_skills = _extract_skills_from_jd(job_description)
    candidate_skills = set(s.lower() for s in (candidate.extracted_skills or []))
    jd_skills_lower = set(s.lower() for s in required_skills)

    matched: set = set()
    if jd_skills_lower:
        matched = jd_skills_lower & candidate_skills
        skill_match = len(matched) / len(jd_skills_lower)
    else:
        skill_match = 0.5

    score = round(skill_match * 100, 1)
    strengths = list(matched)[:5] if matched else ["General experience"]
    gaps = list(jd_skills_lower - candidate_skills)[:5]

    if score >= 70:
        recommendation = "strong_fit"
    elif score >= 40:
        recommendation = "moderate_fit"
    else:
        recommendation = "weak_fit"

    screening = ScreeningResult(
        candidate_id=candidate_id,
        job_description_hash=jd_hash,
        score=score,
        breakdown={
            "skill_match": round(skill_match * 100, 1),
            "experience": 50.0,
            "education": 50.0,
        },
        strengths=strengths,
        gaps=list(gaps),
        recommendation=recommendation,
    )
    db.add(screening)
    await db.flush()

    return {
        "id": str(screening.id),
        "candidate_id": str(candidate_id),
        "score": score,
        "breakdown": screening.breakdown,
        "strengths": strengths,
        "gaps": list(gaps),
        "recommendation": recommendation,
        "created_at": screening.created_at.isoformat() if screening.created_at else None,
    }


def _extract_skills_from_jd(jd_text: str) -> List[str]:
    common_skills = [
        "python", "javascript", "typescript", "react", "angular", "vue", "node",
        "java", "c#", "c++", "go", "rust", "sql", "nosql", "mongodb", "postgresql",
        "aws", "azure", "gcp", "docker", "kubernetes", "terraform", "ci/cd",
        "git", "linux", "rest", "graphql", "api", "machine learning", "deep learning",
        "nlp", "computer vision", "data science", "data engineering", "devops",
        "agile", "scrum", "leadership", "communication", "project management",
        "product management", "ui/ux", "figma", "sketch", "photoshop",
        "html", "css", "sass", "less", "webpack", "babel", "jest", "cypress",
        "selenium", "pytest", "unit testing", "e2e testing",
    ]
    jd_lower = jd_text.lower()
    return [s for s in common_skills if s in jd_lower]


async def rank_candidates(
    db: AsyncSession,
    job_description: str,
    candidate_ids: List[uuid.UUID],
) -> List[Dict[str, Any]]:
    results = []
    for cid in candidate_ids:
        try:
            result = await screen_candidate(db, cid, job_description)
            results.append(result)
        except ValueError:
            continue
    results.sort(key=lambda x: x["score"], reverse=True)
    return results


def _format_result(screening: ScreeningResult) -> Dict[str, Any]:
    return {
        "id": str(screening.id),
        "candidate_id": str(screening.candidate_id),
        "score": screening.score,
        "breakdown": screening.breakdown,
        "strengths": screening.strengths,
        "gaps": screening.gaps,
        "recommendation": screening.recommendation,
        "created_at": screening.created_at.isoformat() if screening.created_at else None,
    }


async def get_screening_history(
    db: AsyncSession,
    candidate_id: uuid.UUID,
) -> List[Dict[str, Any]]:
    result = await db.execute(
        select(ScreeningResult)
        .where(ScreeningResult.candidate_id == candidate_id)
        .order_by(ScreeningResult.created_at.desc())
    )
    return [_format_result(r) for r in result.scalars().all()]
