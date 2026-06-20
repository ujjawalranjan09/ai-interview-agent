"""Interview Template service — CRUD operations for interview templates."""

import uuid
from typing import Any, Dict, List, Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.interview_template import InterviewTemplate


async def create_template(
    db: AsyncSession,
    name: str,
    description: Optional[str],
    user_id: uuid.UUID,
    question_count: int = 10,
    difficulty_level: int = 2,
    question_types: Optional[List[str]] = None,
    skills: Optional[List[str]] = None,
    config: Optional[dict] = None,
    organization_id: Optional[uuid.UUID] = None,
    is_public: bool = False,
) -> InterviewTemplate:
    """Create a new interview template."""
    template = InterviewTemplate(
        name=name,
        description=description,
        question_count=question_count,
        difficulty_level=difficulty_level,
        question_types=question_types or [],
        skills=skills or [],
        config=config or {},
        created_by=user_id,
        organization_id=organization_id,
        is_public=is_public,
    )
    db.add(template)
    await db.flush()
    return template


async def get_template(db: AsyncSession, template_id: uuid.UUID) -> Optional[InterviewTemplate]:
    """Get a template by ID."""
    result = await db.execute(select(InterviewTemplate).where(InterviewTemplate.id == template_id))
    return result.scalar_one_or_none()


async def list_templates(
    db: AsyncSession,
    user_id: uuid.UUID,
    page: int = 1,
    page_size: int = 20,
) -> Dict[str, Any]:
    """List templates for a user."""
    query = select(InterviewTemplate).where(
        (InterviewTemplate.created_by == user_id) | (InterviewTemplate.is_public)
    )
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0
    
    # Paginate
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    templates = list(result.scalars().all())
    
    return {
        "items": templates,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": (total + page_size - 1) // page_size,
    }


async def update_template(
    db: AsyncSession,
    template_id: uuid.UUID,
    name: Optional[str] = None,
    description: Optional[str] = None,
    question_count: Optional[int] = None,
    difficulty_level: Optional[int] = None,
    question_types: Optional[List[str]] = None,
    skills: Optional[List[str]] = None,
    config: Optional[dict] = None,
    is_public: Optional[bool] = None,
) -> Optional[InterviewTemplate]:
    """Update a template."""
    template = await get_template(db, template_id)
    if not template:
        return None
    
    if name is not None:
        template.name = name
    if description is not None:
        template.description = description
    if question_count is not None:
        template.question_count = question_count
    if difficulty_level is not None:
        template.difficulty_level = difficulty_level
    if question_types is not None:
        template.question_types = question_types
    if skills is not None:
        template.skills = skills
    if config is not None:
        template.config = config
    if is_public is not None:
        template.is_public = is_public
    
    await db.flush()
    return template


async def delete_template(db: AsyncSession, template_id: uuid.UUID) -> bool:
    """Delete a template."""
    template = await get_template(db, template_id)
    if not template:
        return False
    
    await db.delete(template)
    await db.flush()
    return True


async def create_interview_from_template(
    db: AsyncSession,
    template_id: uuid.UUID,
    candidate_id: uuid.UUID,
    user_id: uuid.UUID,
) -> uuid.UUID:
    """Create an interview from a template."""
    from app.services.interview_service import create_interview
    from app.schemas.interview import InterviewCreate
    
    template = await get_template(db, template_id)
    if not template:
        raise ValueError("Template not found")
    
    interview_data = InterviewCreate(
        candidate_id=str(candidate_id),
        difficulty_level=template.difficulty_level,
        question_count=template.question_count,
    )
    interview = await create_interview(db, interview_data, user_id)
    
    # Store template reference in interview config
    interview.config = {
        "template_id": str(template.id),
        "template_name": template.name,
        "question_types": template.question_types,
        "skills": template.skills,
    }
    
    await db.flush()
    return interview.id
