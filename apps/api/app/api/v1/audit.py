import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.audit_log import AuditLog

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("/logs", summary="Get audit logs", description="Returns paginated audit log entries with optional filters for action, user, and resource type (admin only).")
async def get_audit_logs(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    action: str | None = Query(None),
    user_id: uuid.UUID | None = Query(None),
    resource_type: str | None = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(100, ge=1, le=500),
):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    query = select(AuditLog)
    count_query = select(func.count()).select_from(AuditLog)
    if action:
        query = query.where(AuditLog.action == action)
        count_query = count_query.where(AuditLog.action == action)
    if user_id:
        query = query.where(AuditLog.user_id == user_id)
        count_query = count_query.where(AuditLog.user_id == user_id)
    if resource_type:
        query = query.where(AuditLog.resource_type == resource_type)
        count_query = count_query.where(AuditLog.resource_type == resource_type)
    total = (await db.execute(count_query)).scalar() or 0
    query = query.order_by(AuditLog.created_at.desc())
    query = query.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    logs = result.scalars().all()
    items = [
        {
            "id": str(log.id),
            "user_id": str(log.user_id) if log.user_id else None,
            "action": log.action,
            "resource_type": log.resource_type,
            "resource_id": log.resource_id,
            "details": log.details,
            "ip_address": log.ip_address,
            "created_at": log.created_at.isoformat() if log.created_at else "",
        }
        for log in logs
    ]
    return {"items": items, "total": total, "page": page, "per_page": per_page}
