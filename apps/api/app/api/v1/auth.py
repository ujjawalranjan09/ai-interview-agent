"""Auth endpoints — register, login, refresh, me."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.rate_limit import rate_limit
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
    verify_token,
)
from app.models.user import User
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse, RefreshRequest
from app.schemas.user import UserResponse, UserUpdate
from app.api.deps import get_current_user
from app.services.audit_service import log_action

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED, summary="Register a new user", description="Creates a new user account and returns JWT access and refresh tokens.")
async def register(
    body: RegisterRequest,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    ip = request.client.host if request.client else "unknown"
    if not rate_limit(f"register:{ip}", 5, 60):
        raise HTTPException(status_code=429, detail="Too many requests")

    result = await db.execute(select(User).where(User.email == body.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    user = User(
        email=body.email,
        password_hash=hash_password(body.password),
        full_name=body.full_name,
        role=body.role,
    )
    db.add(user)
    await db.flush()

    await log_action(db, user.id, "auth.register", "user", str(user.id), {"email": user.email}, ip)

    return TokenResponse(
        access_token=create_access_token(str(user.id)),
        refresh_token=create_refresh_token(str(user.id)),
    )


@router.post("/login", response_model=TokenResponse, summary="Authenticate and log in", description="Validates credentials and returns JWT tokens for an existing user.")
async def login(
    body: LoginRequest,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    ip = request.client.host if request.client else "unknown"
    if not rate_limit(f"login:{ip}", 5, 60):
        raise HTTPException(status_code=429, detail="Too many requests")

    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is inactive")

    await log_action(db, user.id, "auth.login", "user", str(user.id), ip_address=ip)

    return TokenResponse(
        access_token=create_access_token(str(user.id)),
        refresh_token=create_refresh_token(str(user.id)),
    )


@router.post("/refresh", response_model=TokenResponse, summary="Refresh access token", description="Issues a new access token using a valid refresh token.")
async def refresh(body: RefreshRequest, db: Annotated[AsyncSession, Depends(get_db)]):
    try:
        payload = verify_token(body.refresh_token)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    if payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not a refresh token")

    user_id = payload.get("sub")
    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    return TokenResponse(
        access_token=create_access_token(str(user.id)),
        refresh_token=create_refresh_token(str(user.id)),
    )


@router.get("/me", response_model=UserResponse, summary="Get current user profile", description="Returns the authenticated user's profile information.")
async def get_me(current_user: Annotated[User, Depends(get_current_user)]):
    return current_user


@router.put("/me", response_model=UserResponse, summary="Update current user profile", description="Updates the authenticated user's profile fields such as full name and avatar.")
async def update_me(
    body: UserUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    if body.full_name is not None:
        current_user.full_name = body.full_name
    if body.avatar_url is not None:
        current_user.avatar_url = body.avatar_url
    db.add(current_user)
    await db.flush()
    return current_user
