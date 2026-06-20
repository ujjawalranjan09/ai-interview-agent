"""Google OAuth endpoints for Calendar integration."""
import uuid

import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.calendar_credential import CalendarCredential
from app.core.config import settings

router = APIRouter(prefix="/auth/google", tags=["auth"])

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"


@router.get("/calendar")
async def google_calendar_auth(user: User = Depends(get_current_user)):
    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=501, detail="Google OAuth not configured")
    redirect_uri = f"{settings.APP_URL}/api/v1/auth/google/calendar/callback"
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "https://www.googleapis.com/auth/calendar.events",
        "access_type": "offline",
        "state": str(user.id),
    }
    import urllib.parse
    url = f"{GOOGLE_AUTH_URL}?{urllib.parse.urlencode(params)}"
    return {"auth_url": url}


@router.get("/calendar/callback")
async def google_calendar_callback(
    code: str,
    state: str,
    db: AsyncSession = Depends(get_db),
):
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        raise HTTPException(status_code=501, detail="Google OAuth not configured")
    redirect_uri = f"{settings.APP_URL}/api/v1/auth/google/calendar/callback"
    async with httpx.AsyncClient() as client:
        resp = await client.post(GOOGLE_TOKEN_URL, data={
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "code": code,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        })
        if not resp.is_success:
            raise HTTPException(status_code=400, detail="Failed to exchange code")
        tokens = resp.json()
    from datetime import datetime, timedelta, timezone
    credential = CalendarCredential(
        user_id=uuid.UUID(state),
        provider="google",
        access_token=tokens["access_token"],
        refresh_token=tokens.get("refresh_token", ""),
        expires_at=datetime.now(timezone.utc) + timedelta(seconds=tokens.get("expires_in", 3600)),
    )
    db.add(credential)
    await db.flush()
    return {"status": "connected", "provider": "google"}
