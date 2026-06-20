"""Branding service — white-label organization theming."""

import uuid
from typing import Any, Dict, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.branding import OrganizationBranding


async def get_branding(
    db: AsyncSession,
    org_id: uuid.UUID,
) -> Optional[Dict[str, Any]]:
    result = await db.execute(
        select(OrganizationBranding).where(
            OrganizationBranding.organization_id == org_id,
            OrganizationBranding.is_active,
        )
    )
    branding = result.scalar_one_or_none()
    if not branding:
        return None

    return {
        "id": str(branding.id),
        "logo_url": branding.logo_url,
        "favicon_url": branding.favicon_url,
        "primary_color": branding.primary_color,
        "secondary_color": branding.secondary_color,
        "accent_color": branding.accent_color,
        "font_family": branding.font_family,
        "custom_css": branding.custom_css,
        "custom_domain": branding.custom_domain,
        "email_template": branding.email_template,
        "portal_heading": branding.portal_heading,
        "theme_config": branding.theme_config,
    }


async def upsert_branding(
    db: AsyncSession,
    org_id: uuid.UUID,
    data: Dict[str, Any],
) -> Dict[str, Any]:
    result = await db.execute(
        select(OrganizationBranding).where(
            OrganizationBranding.organization_id == org_id
        )
    )
    branding = result.scalar_one_or_none()

    if not branding:
        branding = OrganizationBranding(organization_id=org_id, is_active=True)
        db.add(branding)

    updatable = {
        "logo_url", "favicon_url", "primary_color", "secondary_color",
        "accent_color", "font_family", "custom_css", "custom_domain",
        "email_template", "portal_heading", "is_active", "theme_config",
    }
    for key, value in data.items():
        if key in updatable:
            setattr(branding, key, value)

    await db.flush()
    return await get_branding(db, org_id)


async def get_branding_by_domain(
    db: AsyncSession, domain: str
) -> Optional[Dict[str, Any]]:
    result = await db.execute(
        select(OrganizationBranding).where(
            OrganizationBranding.custom_domain == domain,
            OrganizationBranding.is_active,
        )
    )
    branding = result.scalar_one_or_none()
    if not branding:
        return None
    return {
        "id": str(branding.id),
        "organization_id": str(branding.organization_id),
        "logo_url": branding.logo_url,
        "favicon_url": branding.favicon_url,
        "primary_color": branding.primary_color,
        "secondary_color": branding.secondary_color,
        "accent_color": branding.accent_color,
        "font_family": branding.font_family,
        "custom_css": branding.custom_css,
        "portal_heading": branding.portal_heading,
        "theme_config": branding.theme_config,
    }
