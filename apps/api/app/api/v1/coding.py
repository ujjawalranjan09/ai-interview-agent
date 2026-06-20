"""Coding Interview API endpoints."""

import uuid
from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.services import coding_service
from app.services.audit_service import log_action

router = APIRouter(prefix="/coding", tags=["coding"])


# Request/Response schemas
class CodingQuestionCreate(BaseModel):
    title: str
    description: str
    difficulty: str
    category: str
    language: str = "python"
    starter_code: Optional[str] = None
    solution: Optional[str] = None
    test_cases: Optional[List[dict]] = None
    constraints: Optional[str] = None
    examples: Optional[List[dict]] = None
    tags: Optional[List[str]] = None


class CodingQuestionResponse(BaseModel):
    id: str
    title: str
    description: str
    difficulty: str
    category: str
    language: str
    starter_code: Optional[str]
    solution: Optional[str]
    test_cases: Optional[List[dict]]
    constraints: Optional[str]
    examples: Optional[List[dict]]
    tags: List[str]
    created_at: str


class CodeSubmitRequest(BaseModel):
    code: str
    language: str = "python"


class CodeSubmitResponse(BaseModel):
    submission_id: str
    success: bool
    output: str
    error: Optional[str]
    test_results: List[dict]
    score: float
    passed: bool
    execution_time: float


@router.post("/questions", response_model=CodingQuestionResponse, status_code=status.HTTP_201_CREATED)
async def create_question(
    body: CodingQuestionCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    """Create a new coding question."""
    question = await coding_service.create_question(
        db,
        body.title,
        body.description,
        body.difficulty,
        body.category,
        body.language,
        body.starter_code,
        body.solution,
        body.test_cases,
        body.constraints,
        body.examples,
        body.tags,
        user.id,
    )
    await log_action(db, user.id, "coding.question.create", "coding_question", str(question.id))
    return CodingQuestionResponse(
        id=str(question.id),
        title=question.title,
        description=question.description,
        difficulty=question.difficulty,
        category=question.category,
        language=question.language,
        starter_code=question.starter_code,
        solution=question.solution,
        test_cases=question.test_cases,
        constraints=question.constraints,
        examples=question.examples,
        tags=question.tags or [],
        created_at=question.created_at.isoformat() if question.created_at else "",
    )


@router.get("/questions")
async def list_questions(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    difficulty: Optional[str] = None,
    category: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """List coding questions."""
    result = await coding_service.list_questions(db, difficulty, category, page, page_size)
    return {
        "items": [
            CodingQuestionResponse(
                id=str(q.id),
                title=q.title,
                description=q.description,
                difficulty=q.difficulty,
                category=q.category,
                language=q.language,
                starter_code=q.starter_code,
                solution=q.solution,
                test_cases=q.test_cases,
                constraints=q.constraints,
                examples=q.examples,
                tags=q.tags or [],
                created_at=q.created_at.isoformat() if q.created_at else "",
            )
            for q in result["items"]
        ],
        "total": result["total"],
        "page": result["page"],
        "page_size": result["page_size"],
        "pages": result["pages"],
    }


@router.get("/questions/{question_id}", response_model=CodingQuestionResponse)
async def get_question(
    question_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    """Get a coding question by ID."""
    question = await coding_service.get_question(db, question_id)
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    return CodingQuestionResponse(
        id=str(question.id),
        title=question.title,
        description=question.description,
        difficulty=question.difficulty,
        category=question.category,
        language=question.language,
        starter_code=question.starter_code,
        solution=question.solution,
        test_cases=question.test_cases,
        constraints=question.constraints,
        examples=question.examples,
        tags=question.tags or [],
        created_at=question.created_at.isoformat() if question.created_at else "",
    )


@router.post("/questions/{question_id}/submit", response_model=CodeSubmitResponse)
async def submit_code(
    question_id: uuid.UUID,
    body: CodeSubmitRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    """Submit code for a coding question."""
    # Use a default candidate ID for demo (in production, this would come from auth)
    candidate_id = uuid.uuid4()
    
    try:
        result = await coding_service.submit_code(
            db, question_id, candidate_id, body.code, body.language
        )
        await log_action(
            db, user.id, "coding.submit", "coding_question", str(question_id),
            {"score": result["score"], "passed": result["passed"]}
        )
        return CodeSubmitResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/questions/{question_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_question(
    question_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    """Delete a coding question."""
    success = await coding_service.delete_question(db, question_id)
    if not success:
        raise HTTPException(status_code=404, detail="Question not found")
    await log_action(db, user.id, "coding.question.delete", "coding_question", str(question_id))
