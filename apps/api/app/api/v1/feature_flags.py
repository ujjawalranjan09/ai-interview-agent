"""Feature flag API endpoints."""
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_admin_user
from app.models.user import User
from app.services import feature_flag_service

router = APIRouter(prefix="/feature-flags", tags=["feature-flags"])


@router.get("/")
async def list_flags(
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    return await feature_flag_service.get_all_flags(db)


@router.get("/{key}")
async def get_flag(
    key: str,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    flag = await feature_flag_service.get_flag(db, key)
    if not flag:
        raise HTTPException(status_code=404, detail="Flag not found")
    return flag


@router.get("/{key}/enabled")
async def check_flag(
    key: str,
    db: AsyncSession = Depends(get_db),
):
    enabled = await feature_flag_service.is_enabled(db, key)
    return {"key": key, "enabled": enabled}


@router.post("/")
async def create_flag(
    body: dict,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    flag = await feature_flag_service.create_flag(
        db,
        key=body.get("key", ""),
        name=body.get("name", ""),
        description=body.get("description", ""),
        enabled=body.get("enabled", False),
        enabled_for_roles=body.get("enabled_for_roles", ""),
    )
    return flag


@router.patch("/{key}")
async def update_flag(
    key: str,
    body: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    flag = await feature_flag_service.update_flag(db, key, body)
    if not flag:
        raise HTTPException(status_code=404, detail="Flag not found")
    return flag


@router.delete("/{key}")
async def delete_flag(
    key: str,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    deleted = await feature_flag_service.delete_flag(db, key)
    if not deleted:
        raise HTTPException(status_code=404, detail="Flag not found")
    return {"status": "deleted"}
