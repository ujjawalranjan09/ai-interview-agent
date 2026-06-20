"""Search API endpoints — full-text search across platform entities."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.services import search_service

router = APIRouter(prefix="/search", tags=["search"])


@router.get("")
async def search(
    q: str = Query(..., min_length=1, max_length=200),
    type: str | None = Query(None, alias="type"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await search_service.search_all(q, user, db, search_type=type)
