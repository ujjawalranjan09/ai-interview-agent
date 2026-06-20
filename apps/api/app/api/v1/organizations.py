"""Organization API endpoints."""

import uuid
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.services import org_service
from app.services.audit_service import log_action

router = APIRouter(prefix="/organizations", tags=["organizations"])


# Request/Response schemas
class OrganizationCreate(BaseModel):
    name: str
    description: Optional[str] = None
    website: Optional[str] = None
    industry: Optional[str] = None
    size: Optional[str] = None


class OrganizationUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    website: Optional[str] = None
    industry: Optional[str] = None
    size: Optional[str] = None
    logo_url: Optional[str] = None
    settings: Optional[dict] = None


class OrganizationResponse(BaseModel):
    id: str
    name: str
    slug: str
    description: Optional[str]
    logo_url: Optional[str]
    website: Optional[str]
    industry: Optional[str]
    size: Optional[str]
    settings: Optional[dict]
    is_active: bool
    member_count: int
    created_by: str
    created_at: str


@router.post("", response_model=OrganizationResponse, status_code=status.HTTP_201_CREATED)
async def create_organization(
    body: OrganizationCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    """Create a new organization."""
    org = await org_service.create_organization(
        db, body.name, user.id, body.description, body.website, body.industry, body.size
    )
    await log_action(db, user.id, "org.create", "organization", str(org.id))
    return OrganizationResponse(
        id=str(org.id),
        name=org.name,
        slug=org.slug,
        description=org.description,
        logo_url=org.logo_url,
        website=org.website,
        industry=org.industry,
        size=org.size,
        settings=org.settings,
        is_active=org.is_active,
        member_count=org.member_count or 0,
        created_by=str(org.created_by),
        created_at=org.created_at.isoformat() if org.created_at else "",
    )


@router.get("")
async def list_organizations(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """List all active organizations."""
    result = await org_service.list_organizations(db, page, page_size)
    return {
        "items": [
            OrganizationResponse(
                id=str(o.id),
                name=o.name,
                slug=o.slug,
                description=o.description,
                logo_url=o.logo_url,
                website=o.website,
                industry=o.industry,
                size=o.size,
                settings=o.settings,
                is_active=o.is_active,
                member_count=o.member_count or 0,
                created_by=str(o.created_by),
                created_at=o.created_at.isoformat() if o.created_at else "",
            )
            for o in result["items"]
        ],
        "total": result["total"],
        "page": result["page"],
        "page_size": result["page_size"],
        "pages": result["pages"],
    }


@router.get("/{org_id}", response_model=OrganizationResponse)
async def get_organization(
    org_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    """Get an organization by ID."""
    org = await org_service.get_organization(db, org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    return OrganizationResponse(
        id=str(org.id),
        name=org.name,
        slug=org.slug,
        description=org.description,
        logo_url=org.logo_url,
        website=org.website,
        industry=org.industry,
        size=org.size,
        settings=org.settings,
        is_active=org.is_active,
        member_count=org.member_count or 0,
        created_by=str(org.created_by),
        created_at=org.created_at.isoformat() if org.created_at else "",
    )


@router.get("/slug/{slug}", response_model=OrganizationResponse)
async def get_organization_by_slug(
    slug: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    """Get an organization by slug."""
    org = await org_service.get_organization_by_slug(db, slug)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    return OrganizationResponse(
        id=str(org.id),
        name=org.name,
        slug=org.slug,
        description=org.description,
        logo_url=org.logo_url,
        website=org.website,
        industry=org.industry,
        size=org.size,
        settings=org.settings,
        is_active=org.is_active,
        member_count=org.member_count or 0,
        created_by=str(org.created_by),
        created_at=org.created_at.isoformat() if org.created_at else "",
    )


@router.patch("/{org_id}", response_model=OrganizationResponse)
async def update_organization(
    org_id: uuid.UUID,
    body: OrganizationUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    """Update an organization."""
    org = await org_service.update_organization(
        db, org_id, body.name, body.description, body.website,
        body.industry, body.size, body.logo_url, body.settings
    )
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    return OrganizationResponse(
        id=str(org.id),
        name=org.name,
        slug=org.slug,
        description=org.description,
        logo_url=org.logo_url,
        website=org.website,
        industry=org.industry,
        size=org.size,
        settings=org.settings,
        is_active=org.is_active,
        member_count=org.member_count or 0,
        created_by=str(org.created_by),
        created_at=org.created_at.isoformat() if org.created_at else "",
    )


@router.delete("/{org_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_organization(
    org_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    """Soft delete an organization."""
    success = await org_service.delete_organization(db, org_id)
    if not success:
        raise HTTPException(status_code=404, detail="Organization not found")
    await log_action(db, user.id, "org.delete", "organization", str(org_id))
