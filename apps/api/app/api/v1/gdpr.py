"""GDPR compliance API endpoints."""
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.services import gdpr_service

router = APIRouter(prefix="/gdpr", tags=["gdpr"])


@router.get("/consents")
async def list_consents(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await gdpr_service.get_consents(db, user.id)


@router.put("/consents")
async def update_consent(
    body: dict,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await gdpr_service.update_consent(
        db,
        user.id,
        body["consent_type"],
        body["granted"],
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )


@router.post("/export")
async def request_export(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await gdpr_service.request_data_export(db, user.id)


@router.get("/export")
async def export_status(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await gdpr_service.get_export_status(db, user.id)


@router.delete("/data")
async def delete_data(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await gdpr_service.delete_user_data(db, user.id)


@router.get("/retention")
async def list_policies(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    org_id = getattr(user, "organization_id", None)
    return await gdpr_service.get_retention_policies(db, org_id)


@router.put("/retention")
async def update_policy(
    body: dict,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    org_id = getattr(user, "organization_id", None)
    if not org_id:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="No organization associated")
    return await gdpr_service.update_retention_policy(
        db, org_id, body["entity_type"], body["retention_days"], body.get("auto_delete", False)
    )
