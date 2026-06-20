"""Question Bank API endpoints."""

import uuid
from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.services import question_bank_service
from app.services.audit_service import log_action

router = APIRouter(prefix="/banks", tags=["question-banks"])


# Request/Response schemas
class BankCreate(BaseModel):
    name: str
    description: Optional[str] = None
    category: str
    is_public: bool = False


class BankResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    category: str
    question_count: int
    is_public: bool
    created_by: str
    created_at: str


class BankQuestionCreate(BaseModel):
    question_text: str
    question_type: str
    difficulty: str
    reference_answer: Optional[str] = None
    keywords: Optional[List[str]] = None
    concepts: Optional[List[str]] = None
    tags: Optional[List[str]] = None


class BankQuestionResponse(BaseModel):
    id: str
    bank_id: str
    question_text: str
    question_type: str
    difficulty: str
    reference_answer: Optional[str]
    keywords: Optional[List[str]]
    concepts: Optional[List[str]]
    tags: List[str]
    source_interview_id: Optional[str]
    created_at: str


class GenerateInterviewRequest(BaseModel):
    candidate_id: str
    count: int = 10
    difficulty: Optional[str] = None


@router.post("", response_model=BankResponse, status_code=status.HTTP_201_CREATED)
async def create_bank(
    body: BankCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    """Create a new question bank."""
    bank = await question_bank_service.create_bank(
        db, body.name, body.description, body.category, user.id
    )
    await log_action(db, user.id, "bank.create", "question_bank", str(bank.id))
    return BankResponse(
        id=str(bank.id),
        name=bank.name,
        description=bank.description,
        category=bank.category,
        question_count=bank.question_count or 0,
        is_public=bank.is_public,
        created_by=str(bank.created_by),
        created_at=bank.created_at.isoformat() if bank.created_at else "",
    )


@router.get("")
async def list_banks(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    category: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """List question banks for the current user."""
    result = await question_bank_service.list_banks(
        db, user.id, category, page, page_size
    )
    return {
        "items": [
            BankResponse(
                id=str(b.id),
                name=b.name,
                description=b.description,
                category=b.category,
                question_count=b.question_count or 0,
                is_public=b.is_public,
                created_by=str(b.created_by),
                created_at=b.created_at.isoformat() if b.created_at else "",
            )
            for b in result["items"]
        ],
        "total": result["total"],
        "page": result["page"],
        "page_size": result["page_size"],
        "pages": result["pages"],
    }


@router.get("/{bank_id}")
async def get_bank(
    bank_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    """Get a question bank by ID."""
    bank = await question_bank_service.get_bank(db, bank_id)
    if not bank:
        raise HTTPException(status_code=404, detail="Bank not found")
    return BankResponse(
        id=str(bank.id),
        name=bank.name,
        description=bank.description,
        category=bank.category,
        question_count=bank.question_count or 0,
        is_public=bank.is_public,
        created_by=str(bank.created_by),
        created_at=bank.created_at.isoformat() if bank.created_at else "",
    )


@router.post("/{bank_id}/questions", response_model=BankQuestionResponse, status_code=status.HTTP_201_CREATED)
async def add_question(
    bank_id: uuid.UUID,
    body: BankQuestionCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    """Add a question to a bank."""
    bank = await question_bank_service.get_bank(db, bank_id)
    if not bank:
        raise HTTPException(status_code=404, detail="Bank not found")
    
    question = await question_bank_service.add_question_to_bank(
        db,
        bank_id,
        body.question_text,
        body.question_type,
        body.difficulty,
        body.reference_answer,
        body.keywords,
        body.concepts,
        body.tags,
    )
    await log_action(db, user.id, "bank.question.add", "bank_question", str(question.id))
    return BankQuestionResponse(
        id=str(question.id),
        bank_id=str(question.bank_id),
        question_text=question.question_text,
        question_type=question.question_type,
        difficulty=question.difficulty,
        reference_answer=question.reference_answer,
        keywords=question.keywords,
        concepts=question.concepts,
        tags=question.tags or [],
        source_interview_id=str(question.source_interview_id) if question.source_interview_id else None,
        created_at=question.created_at.isoformat() if question.created_at else "",
    )


@router.get("/{bank_id}/questions")
async def list_bank_questions(
    bank_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    difficulty: Optional[str] = None,
    question_type: Optional[str] = None,
):
    """List questions in a bank."""
    bank = await question_bank_service.get_bank(db, bank_id)
    if not bank:
        raise HTTPException(status_code=404, detail="Bank not found")
    
    result = await question_bank_service.get_bank_questions(
        db, bank_id, page, page_size, difficulty, question_type
    )
    return {
        "items": [
            BankQuestionResponse(
                id=str(q.id),
                bank_id=str(q.bank_id),
                question_text=q.question_text,
                question_type=q.question_type,
                difficulty=q.difficulty,
                reference_answer=q.reference_answer,
                keywords=q.keywords,
                concepts=q.concepts,
                tags=q.tags or [],
                source_interview_id=str(q.source_interview_id) if q.source_interview_id else None,
                created_at=q.created_at.isoformat() if q.created_at else "",
            )
            for q in result["items"]
        ],
        "total": result["total"],
        "page": result["page"],
        "page_size": result["page_size"],
        "pages": result["pages"],
    }


@router.post("/{bank_id}/import/{interview_id}")
async def import_from_interview(
    bank_id: uuid.UUID,
    interview_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    """Import questions from an existing interview into a bank."""
    bank = await question_bank_service.get_bank(db, bank_id)
    if not bank:
        raise HTTPException(status_code=404, detail="Bank not found")
    
    imported = await question_bank_service.import_questions_from_interview(
        db, bank_id, interview_id
    )
    await log_action(
        db, user.id, "bank.import", "question_bank", str(bank_id),
        {"interview_id": str(interview_id), "count": len(imported)}
    )
    return {"imported": len(imported)}


@router.post("/{bank_id}/generate-interview")
async def generate_interview(
    bank_id: uuid.UUID,
    body: GenerateInterviewRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    """Generate an interview using questions from a bank."""
    bank = await question_bank_service.get_bank(db, bank_id)
    if not bank:
        raise HTTPException(status_code=404, detail="Bank not found")
    
    try:
        interview_id = await question_bank_service.generate_interview_from_bank(
            db, bank_id, uuid.UUID(body.candidate_id), user.id, body.count, body.difficulty
        )
        await log_action(
            db, user.id, "bank.generate", "question_bank", str(bank_id),
            {"interview_id": str(interview_id)}
        )
        return {"interview_id": str(interview_id)}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{bank_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_bank(
    bank_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    """Delete a question bank."""
    success = await question_bank_service.delete_bank(db, bank_id)
    if not success:
        raise HTTPException(status_code=404, detail="Bank not found")
    await log_action(db, user.id, "bank.delete", "question_bank", str(bank_id))
