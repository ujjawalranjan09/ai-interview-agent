"""GDPR compliance service — consent management, data export, deletion."""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.consent import Consent, DataRetentionPolicy, DataExportRequest


async def get_consents(db: AsyncSession, user_id: uuid.UUID) -> List[Dict[str, Any]]:
    result = await db.execute(
        select(Consent).where(Consent.user_id == user_id).order_by(Consent.created_at.desc())
    )
    return [
        {
            "id": str(c.id),
            "consent_type": c.consent_type,
            "granted": c.granted,
            "granted_at": c.granted_at.isoformat() if c.granted_at else None,
            "revoked_at": c.revoked_at.isoformat() if c.revoked_at else None,
        }
        for c in result.scalars().all()
    ]


async def update_consent(
    db: AsyncSession,
    user_id: uuid.UUID,
    consent_type: str,
    granted: bool,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> Dict[str, Any]:
    result = await db.execute(
        select(Consent).where(
            Consent.user_id == user_id, Consent.consent_type == consent_type
        )
    )
    consent = result.scalar_one_or_none()
    now = datetime.utcnow()
    if not consent:
        consent = Consent(
            user_id=user_id,
            consent_type=consent_type,
            granted=granted,
            ip_address=ip_address,
            user_agent=user_agent,
            granted_at=now if granted else None,
            revoked_at=None if granted else None,
        )
        db.add(consent)
    else:
        consent.granted = granted
        consent.ip_address = ip_address
        consent.user_agent = user_agent
        consent.granted_at = now if granted else None
        consent.revoked_at = None if granted else now
    await db.flush()
    return {
        "id": str(consent.id),
        "consent_type": consent.consent_type,
        "granted": consent.granted,
    }


async def request_data_export(
    db: AsyncSession, user_id: uuid.UUID
) -> Dict[str, Any]:
    existing = await db.execute(
        select(DataExportRequest).where(
            DataExportRequest.user_id == user_id,
            DataExportRequest.status == "pending",
        )
    )
    if existing.scalar_one_or_none():
        return {"status": "in_progress", "message": "Export already in progress"}

    request = DataExportRequest(user_id=user_id, status="pending")
    db.add(request)
    await db.flush()
    return {"id": str(request.id), "status": "pending"}


async def get_export_status(
    db: AsyncSession, user_id: uuid.UUID
) -> List[Dict[str, Any]]:
    result = await db.execute(
        select(DataExportRequest)
        .where(DataExportRequest.user_id == user_id)
        .order_by(DataExportRequest.created_at.desc())
        .limit(10)
    )
    return [
        {
            "id": str(r.id),
            "status": r.status,
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "expires_at": r.expires_at.isoformat() if r.expires_at else None,
        }
        for r in result.scalars().all()
    ]


async def delete_user_data(db: AsyncSession, user_id: uuid.UUID) -> Dict[str, Any]:
    await db.execute(delete(Consent).where(Consent.user_id == user_id))
    await db.execute(
        delete(DataExportRequest).where(DataExportRequest.user_id == user_id)
    )
    await db.flush()
    return {"status": "deleted"}


async def get_retention_policies(
    db: AsyncSession, org_id: Optional[uuid.UUID] = None
) -> List[Dict[str, Any]]:
    stmt = select(DataRetentionPolicy)
    if org_id:
        stmt = stmt.where(DataRetentionPolicy.organization_id == org_id)
    result = await db.execute(stmt)
    return [
        {
            "id": str(p.id),
            "entity_type": p.entity_type,
            "retention_days": p.retention_days,
            "auto_delete": p.auto_delete,
        }
        for p in result.scalars().all()
    ]


async def update_retention_policy(
    db: AsyncSession,
    org_id: uuid.UUID,
    entity_type: str,
    retention_days: int,
    auto_delete: bool = False,
) -> Dict[str, Any]:
    result = await db.execute(
        select(DataRetentionPolicy).where(
            DataRetentionPolicy.organization_id == org_id,
            DataRetentionPolicy.entity_type == entity_type,
        )
    )
    policy = result.scalar_one_or_none()
    if not policy:
        policy = DataRetentionPolicy(
            organization_id=org_id,
            entity_type=entity_type,
            retention_days=retention_days,
            auto_delete=auto_delete,
        )
        db.add(policy)
    else:
        policy.retention_days = retention_days
        policy.auto_delete = auto_delete
    await db.flush()
    return {
        "id": str(policy.id),
        "entity_type": policy.entity_type,
        "retention_days": policy.retention_days,
        "auto_delete": policy.auto_delete,
    }
