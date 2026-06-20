import uuid
from typing import Annotated
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.interview import Interview
from app.models.candidate import Candidate
from app.schemas.admin import (
    UserListItem,
    UserListResponse,
    UserUpdateRequest,
    SystemHealthResponse,
    SystemStatsResponse,
)
from app.services.audit_service import log_action

router = APIRouter(prefix="/admin", tags=["admin"])


async def _require_admin(user: User):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")


@router.get("/users", response_model=UserListResponse, summary="List users", description="Returns a paginated list of all users with optional role and status filters (admin only).")
async def list_users(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    role: str | None = Query(None),
    is_active: bool | None = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
):
    await _require_admin(user)

    query = select(User)
    count_query = select(func.count()).select_from(User)

    if role:
        query = query.where(User.role == role)
        count_query = count_query.where(User.role == role)
    if is_active is not None:
        query = query.where(User.is_active == is_active)
        count_query = count_query.where(User.is_active == is_active)

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = query.order_by(User.created_at.desc())
    query = query.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    users = result.scalars().all()

    items = [
        UserListItem(
            id=str(u.id),
            email=u.email,
            full_name=u.full_name,
            role=u.role,
            is_active=u.is_active,
            created_at=u.created_at.isoformat() if u.created_at else "",
        )
        for u in users
    ]
    return UserListResponse(items=items, total=total, page=page, per_page=per_page)


@router.patch("/users/{user_id}", response_model=UserListItem, summary="Update a user", description="Updates a user's role or active status (admin only).")
async def update_user(
    user_id: uuid.UUID,
    body: UserUpdateRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    curr_user: Annotated[User, Depends(get_current_user)],
):
    await _require_admin(curr_user)

    result = await db.execute(select(User).where(User.id == user_id))
    target = result.scalar_one_or_none()
    if not target:
        raise HTTPException(status_code=404, detail="User not found")

    if user_id == curr_user.id and body.is_active is False:
        raise HTTPException(status_code=400, detail="Cannot deactivate yourself")

    if body.role is not None:
        if body.role not in ("admin", "interviewer", "candidate"):
            raise HTTPException(status_code=400, detail="Invalid role")
        target.role = body.role
    if body.is_active is not None:
        target.is_active = body.is_active

    await log_action(db, curr_user.id, "admin.update_user", "user", str(user_id), {"role": body.role, "is_active": body.is_active})
    await db.commit()

    return UserListItem(
        id=str(target.id),
        email=target.email,
        full_name=target.full_name,
        role=target.role,
        is_active=target.is_active,
        created_at=target.created_at.isoformat() if target.created_at else "",
    )


@router.get("/system/health", response_model=SystemHealthResponse, summary="System health check", description="Checks the status of the database connection and overall system health (admin only).")
async def system_health(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    await _require_admin(user)
    try:
        await db.execute(text("SELECT 1"))
        database = "connected"
    except Exception:
        database = "error"

    return SystemHealthResponse(
        status="healthy" if database == "connected" else "unhealthy",
        database=database,
        timestamp=datetime.utcnow().isoformat(),
    )


@router.get("/system/stats", response_model=SystemStatsResponse, summary="System statistics", description="Returns aggregate system stats including total users, interviews, candidates, and active sessions (admin only).")
async def system_stats(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    await _require_admin(user)

    users = await db.execute(select(func.count()).select_from(User))
    interviews = await db.execute(select(func.count()).select_from(Interview))
    candidates = await db.execute(select(func.count()).select_from(Candidate))
    active = await db.execute(
        select(func.count()).select_from(Interview).where(Interview.status == "in_progress")
    )

    return SystemStatsResponse(
        total_users=users.scalar() or 0,
        total_interviews=interviews.scalar() or 0,
        total_candidates=candidates.scalar() or 0,
        active_sessions=active.scalar() or 0,
    )
