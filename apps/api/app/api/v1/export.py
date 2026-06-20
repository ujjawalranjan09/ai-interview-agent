from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.services import export_service

router = APIRouter(prefix="/export", tags=["export"])


@router.get("/candidates", summary="Export candidates as CSV", description="Exports all candidate records as a CSV file download.")
async def export_candidates(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    if user.role not in ("admin", "interviewer"):
        raise HTTPException(status_code=403, detail="Not allowed")
    csv_bytes = await export_service.export_candidates_csv(db)
    return Response(
        content=csv_bytes,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=candidates_export.csv"},
    )


@router.get("/interviews", summary="Export interviews as CSV", description="Exports interview records as a CSV file download with optional status and date range filters.")
async def export_interviews(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    status: str | None = Query(None),
    date_from: str | None = Query(None),
    date_to: str | None = Query(None),
):
    if user.role not in ("admin", "interviewer"):
        raise HTTPException(status_code=403, detail="Not allowed")
    csv_bytes = await export_service.export_interviews_csv(db, status, date_from, date_to)
    return Response(
        content=csv_bytes,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=interviews_export.csv"},
    )
