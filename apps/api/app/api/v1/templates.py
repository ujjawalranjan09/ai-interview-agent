"""Interview Template API endpoints."""

import uuid
from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.services import template_service
from app.services.audit_service import log_action

router = APIRouter(prefix="/templates", tags=["templates"])


# Request/Response schemas
class TemplateCreate(BaseModel):
    name: str
    description: Optional[str] = None
    question_count: int = 10
    difficulty_level: int = 2
    question_types: Optional[List[str]] = None
    skills: Optional[List[str]] = None
    config: Optional[dict] = None
    is_public: bool = False


class TemplateUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    question_count: Optional[int] = None
    difficulty_level: Optional[int] = None
    question_types: Optional[List[str]] = None
    skills: Optional[List[str]] = None
    config: Optional[dict] = None
    is_public: Optional[bool] = None


class TemplateResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    question_count: int
    difficulty_level: int
    question_types: List[str]
    skills: List[str]
    config: Optional[dict]
    is_public: bool
    created_by: str
    created_at: str


class CreateFromTemplateRequest(BaseModel):
    candidate_id: str


@router.post("", response_model=TemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_template(
    body: TemplateCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    """Create a new interview template."""
    template = await template_service.create_template(
        db,
        body.name,
        body.description,
        user.id,
        body.question_count,
        body.difficulty_level,
        body.question_types,
        body.skills,
        body.config,
        is_public=body.is_public,
    )
    await log_action(db, user.id, "template.create", "template", str(template.id))
    return TemplateResponse(
        id=str(template.id),
        name=template.name,
        description=template.description,
        question_count=template.question_count,
        difficulty_level=template.difficulty_level,
        question_types=template.question_types or [],
        skills=template.skills or [],
        config=template.config,
        is_public=template.is_public,
        created_by=str(template.created_by),
        created_at=template.created_at.isoformat() if template.created_at else "",
    )


@router.get("")
async def list_templates(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """List interview templates for the current user."""
    result = await template_service.list_templates(db, user.id, page, page_size)
    return {
        "items": [
            TemplateResponse(
                id=str(t.id),
                name=t.name,
                description=t.description,
                question_count=t.question_count,
                difficulty_level=t.difficulty_level,
                question_types=t.question_types or [],
                skills=t.skills or [],
                config=t.config,
                is_public=t.is_public,
                created_by=str(t.created_by),
                created_at=t.created_at.isoformat() if t.created_at else "",
            )
            for t in result["items"]
        ],
        "total": result["total"],
        "page": result["page"],
        "page_size": result["page_size"],
        "pages": result["pages"],
    }


@router.get("/{template_id}", response_model=TemplateResponse)
async def get_template(
    template_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    """Get a template by ID."""
    template = await template_service.get_template(db, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return TemplateResponse(
        id=str(template.id),
        name=template.name,
        description=template.description,
        question_count=template.question_count,
        difficulty_level=template.difficulty_level,
        question_types=template.question_types or [],
        skills=template.skills or [],
        config=template.config,
        is_public=template.is_public,
        created_by=str(template.created_by),
        created_at=template.created_at.isoformat() if template.created_at else "",
    )


@router.patch("/{template_id}", response_model=TemplateResponse)
async def update_template(
    template_id: uuid.UUID,
    body: TemplateUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    """Update a template."""
    template = await template_service.update_template(
        db,
        template_id,
        body.name,
        body.description,
        body.question_count,
        body.difficulty_level,
        body.question_types,
        body.skills,
        body.config,
        body.is_public,
    )
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return TemplateResponse(
        id=str(template.id),
        name=template.name,
        description=template.description,
        question_count=template.question_count,
        difficulty_level=template.difficulty_level,
        question_types=template.question_types or [],
        skills=template.skills or [],
        config=template.config,
        is_public=template.is_public,
        created_by=str(template.created_by),
        created_at=template.created_at.isoformat() if template.created_at else "",
    )


@router.post("/{template_id}/create-interview")
async def create_interview_from_template(
    template_id: uuid.UUID,
    body: CreateFromTemplateRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    """Create an interview from a template."""
    try:
        interview_id = await template_service.create_interview_from_template(
            db, template_id, uuid.UUID(body.candidate_id), user.id
        )
        await log_action(
            db, user.id, "template.use", "template", str(template_id),
            {"interview_id": str(interview_id)}
        )
        return {"interview_id": str(interview_id)}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_template(
    template_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    """Delete a template."""
    success = await template_service.delete_template(db, template_id)
    if not success:
        raise HTTPException(status_code=404, detail="Template not found")
    await log_action(db, user.id, "template.delete", "template", str(template_id))
