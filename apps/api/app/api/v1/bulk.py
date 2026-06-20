"""Bulk operations API endpoints."""
import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.services import bulk_service

router = APIRouter(prefix="/bulk", tags=["bulk"])


@router.post("/import/candidates")
async def bulk_import_candidates(
    body: dict,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    org_id = getattr(user, "organization_id", None)
    return await bulk_service.bulk_import_candidates(db, org_id, body.get("candidates", []))


@router.put("/interviews")
async def bulk_update_interviews(
    body: dict,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    ids = [uuid.UUID(id) for id in body.get("ids", [])]
    updates = body.get("updates", {})
    return await bulk_service.bulk_update_interviews(db, ids, updates)


@router.post("/delete")
async def bulk_delete(
    body: dict,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    ids = [uuid.UUID(id) for id in body.get("ids", [])]
    return await bulk_service.bulk_delete(db, body.get("entity_type", ""), ids)


@router.post("/status")
async def bulk_status(
    body: dict,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    ids = [uuid.UUID(id) for id in body.get("ids", [])]
    return await bulk_service.bulk_get_status(db, body.get("entity_type", ""), ids)
