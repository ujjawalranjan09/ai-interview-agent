"""Health check endpoints."""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check():
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": "ai-interview-agent",
    }


@router.get("/health/ready")
async def readiness_check(db: AsyncSession = Depends(get_db)):
    try:
        await db.execute(text("SELECT 1"))
        db_status = "ok"
    except Exception:
        db_status = "error"
    return {
        "status": "ok" if db_status == "ok" else "degraded",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "checks": {"database": db_status},
    }
