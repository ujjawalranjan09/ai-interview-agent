"""Organization service — CRUD operations for organizations."""

import re
import uuid
from typing import Any, Dict, Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.organization import Organization


def generate_slug(name: str) -> str:
    """Generate a URL-safe slug from organization name."""
    slug = name.lower().strip()
    slug = re.sub(r'[^\w\s-]', '', slug)
    slug = re.sub(r'[-\s]+', '-', slug)
    return slug[:128]


async def create_organization(
    db: AsyncSession,
    name: str,
    user_id: uuid.UUID,
    description: Optional[str] = None,
    website: Optional[str] = None,
    industry: Optional[str] = None,
    size: Optional[str] = None,
) -> Organization:
    """Create a new organization."""
    slug = generate_slug(name)
    
    # Ensure unique slug
    existing = await db.execute(select(Organization).where(Organization.slug == slug))
    if existing.scalar_one_or_none():
        counter = 1
        while True:
            test_slug = f"{slug}-{counter}"
            existing = await db.execute(select(Organization).where(Organization.slug == test_slug))
            if not existing.scalar_one_or_none():
                slug = test_slug
                break
            counter += 1
    
    org = Organization(
        name=name,
        slug=slug,
        description=description,
        website=website,
        industry=industry,
        size=size,
        created_by=user_id,
        member_count=1,
    )
    db.add(org)
    await db.flush()
    return org


async def get_organization(db: AsyncSession, org_id: uuid.UUID) -> Optional[Organization]:
    """Get an organization by ID."""
    result = await db.execute(select(Organization).where(Organization.id == org_id))
    return result.scalar_one_or_none()


async def get_organization_by_slug(db: AsyncSession, slug: str) -> Optional[Organization]:
    """Get an organization by slug."""
    result = await db.execute(select(Organization).where(Organization.slug == slug))
    return result.scalar_one_or_none()


async def list_organizations(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 20,
) -> Dict[str, Any]:
    """List all active organizations."""
    query = select(Organization).where(Organization.is_active)
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0
    
    # Paginate
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    orgs = list(result.scalars().all())
    
    return {
        "items": orgs,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": (total + page_size - 1) // page_size,
    }


async def update_organization(
    db: AsyncSession,
    org_id: uuid.UUID,
    name: Optional[str] = None,
    description: Optional[str] = None,
    website: Optional[str] = None,
    industry: Optional[str] = None,
    size: Optional[str] = None,
    logo_url: Optional[str] = None,
    settings: Optional[dict] = None,
) -> Optional[Organization]:
    """Update an organization."""
    org = await get_organization(db, org_id)
    if not org:
        return None
    
    if name is not None:
        org.name = name
        # Update slug if name changes
        new_slug = generate_slug(name)
        if new_slug != org.slug:
            existing = await db.execute(select(Organization).where(Organization.slug == new_slug))
            if not existing.scalar_one_or_none():
                org.slug = new_slug
    if description is not None:
        org.description = description
    if website is not None:
        org.website = website
    if industry is not None:
        org.industry = industry
    if size is not None:
        org.size = size
    if logo_url is not None:
        org.logo_url = logo_url
    if settings is not None:
        org.settings = settings
    
    await db.flush()
    return org


async def delete_organization(db: AsyncSession, org_id: uuid.UUID) -> bool:
    """Soft delete an organization."""
    org = await get_organization(db, org_id)
    if not org:
        return False
    
    org.is_active = False
    await db.flush()
    return True


async def add_member(db: AsyncSession, org_id: uuid.UUID) -> Optional[Organization]:
    """Increment member count."""
    org = await get_organization(db, org_id)
    if not org:
        return None
    
    org.member_count = (org.member_count or 0) + 1
    await db.flush()
    return org


async def remove_member(db: AsyncSession, org_id: uuid.UUID) -> Optional[Organization]:
    """Decrement member count."""
    org = await get_organization(db, org_id)
    if not org:
        return None
    
    org.member_count = max(0, (org.member_count or 1) - 1)
    await db.flush()
    return org
