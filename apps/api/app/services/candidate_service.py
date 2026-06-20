"""Candidate service — CRUD + resume upload."""

import uuid

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.candidate import Candidate
from app.schemas.candidate import CandidateCreate, CandidateUpdate


async def create_candidate(db: AsyncSession, data: CandidateCreate) -> Candidate:
    candidate = Candidate(name=data.name, email=data.email)
    db.add(candidate)
    await db.flush()
    return candidate


async def get_candidate(db: AsyncSession, candidate_id: uuid.UUID) -> Candidate | None:
    result = await db.execute(select(Candidate).where(Candidate.id == candidate_id))
    return result.scalar_one_or_none()


async def list_candidates(
    db: AsyncSession, page: int = 1, page_size: int = 20, search: str | None = None,
) -> dict:
    query = select(Candidate)
    count_query = select(func.count()).select_from(Candidate)

    if search:
        pattern = f"%{search}%"
        query = query.where(Candidate.name.ilike(pattern) | Candidate.email.ilike(pattern))
        count_query = count_query.where(Candidate.name.ilike(pattern) | Candidate.email.ilike(pattern))

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = query.order_by(Candidate.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    items = list(result.scalars().all())

    return {"items": items, "total": total, "page": page, "page_size": page_size}


async def update_candidate(db: AsyncSession, candidate_id: uuid.UUID, data: CandidateUpdate) -> Candidate | None:
    candidate = await get_candidate(db, candidate_id)
    if not candidate:
        return None
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(candidate, key, value)
    await db.flush()
    return candidate


async def upload_resume(db: AsyncSession, candidate_id: uuid.UUID, file_bytes: bytes, filename: str) -> Candidate | None:
    candidate = await get_candidate(db, candidate_id)
    if not candidate:
        return None

    from app.core.s3 import upload_file
    import os

    ext = os.path.splitext(filename)[1] or ".pdf"
    s3_key = f"resumes/{candidate_id}{ext}"
    upload_file(file_bytes, s3_key, "application/pdf")
    candidate.resume_s3_key = s3_key

    from app.services.resume_service import process_resume
    result = process_resume(file_bytes)
    candidate.extracted_skills = result["skills"]
    candidate.extracted_projects = result["projects"]

    await db.flush()
    return candidate
