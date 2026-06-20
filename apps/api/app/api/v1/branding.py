"""Branding API endpoints — white-label theming."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.services import branding_service

router = APIRouter(prefix="/branding", tags=["branding"])


@router.get("")
async def get_branding(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    org_id = getattr(user, "organization_id", None)
    if not org_id:
        raise HTTPException(status_code=400, detail="No organization associated")
    branding = await branding_service.get_branding(db, org_id)
    if not branding:
        return {}
    return branding


@router.put("")
async def upsert_branding(
    body: dict,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    org_id = getattr(user, "organization_id", None)
    if not org_id:
        raise HTTPException(status_code=400, detail="No organization associated")
    return await branding_service.upsert_branding(db, org_id, body)


@router.get("/by-domain")
async def get_branding_by_domain(
    domain: str,
    db: AsyncSession = Depends(get_db),
):
    branding = await branding_service.get_branding_by_domain(db, domain)
    if not branding:
        raise HTTPException(status_code=404, detail="No branding found for domain")
    return branding
