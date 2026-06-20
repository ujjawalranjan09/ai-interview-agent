"""Bulk operations service — batch import and operations."""

import uuid
from typing import Any, Dict, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.candidate import Candidate
from app.models.interview import Interview


async def bulk_import_candidates(
    db: AsyncSession,
    org_id: uuid.UUID,
    candidates: List[Dict[str, Any]],
) -> Dict[str, Any]:
    created = []
    errors = []
    for i, c in enumerate(candidates):
        try:
            candidate = Candidate(
                name=c.get("name", ""),
                email=c.get("email"),
                extracted_skills=c.get("skills"),
            )
            db.add(candidate)
            created.append({"index": i, "id": str(candidate.id)})
        except Exception as e:
            errors.append({"index": i, "error": str(e)})
    await db.flush()
    return {"created": len(created), "errors": errors, "items": created}


async def bulk_update_interviews(
    db: AsyncSession,
    interview_ids: List[uuid.UUID],
    updates: Dict[str, Any],
) -> Dict[str, Any]:
    updated = 0
    errors = []
    for id in interview_ids:
        try:
            result = await db.execute(select(Interview).where(Interview.id == id))
            interview = result.scalar_one_or_none()
            if not interview:
                errors.append({"id": str(id), "error": "Not found"})
                continue

            allowed_fields = {"status", "difficulty_level", "question_count"}
            for key, value in updates.items():
                if key in allowed_fields:
                    setattr(interview, key, value)
            updated += 1
        except Exception as e:
            errors.append({"id": str(id), "error": str(e)})
    await db.flush()
    return {"updated": updated, "errors": errors}


async def bulk_delete(
    db: AsyncSession,
    entity_type: str,
    ids: List[uuid.UUID],
) -> Dict[str, Any]:

    model_map = {
        "candidates": Candidate,
        "interviews": Interview,
    }
    model = model_map.get(entity_type)
    if not model:
        return {"deleted": 0, "errors": [{"error": f"Unknown entity type: {entity_type}"}]}

    deleted = 0
    errors = []
    for id in ids:
        try:
            result = await db.execute(select(model).where(model.id == id))
            obj = result.scalar_one_or_none()
            if not obj:
                errors.append({"id": str(id), "error": "Not found"})
                continue
            await db.delete(obj)
            deleted += 1
        except Exception as e:
            errors.append({"id": str(id), "error": str(e)})
    await db.flush()
    return {"deleted": deleted, "errors": errors}


async def bulk_get_status(
    db: AsyncSession,
    entity_type: str,
    ids: List[uuid.UUID],
) -> List[Dict[str, Any]]:
    model_map = {
        "candidates": Candidate,
        "interviews": Interview,
    }
    model = model_map.get(entity_type)
    if not model:
        return [{"error": f"Unknown entity type: {entity_type}"}]

    results = []
    for id in ids:
        result = await db.execute(select(model).where(model.id == id))
        obj = result.scalar_one_or_none()
        if obj:
            results.append({"id": str(id), "exists": True, "status": getattr(obj, "status", None)})
        else:
            results.append({"id": str(id), "exists": False})
    return results
