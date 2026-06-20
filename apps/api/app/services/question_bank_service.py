"""Question Bank service — CRUD operations for question banks."""

import uuid
from typing import Any, Dict, List, Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.question_bank import QuestionBank, BankQuestion
from app.models.question import Question


async def create_bank(
    db: AsyncSession,
    name: str,
    description: Optional[str],
    category: str,
    user_id: uuid.UUID,
    organization_id: Optional[uuid.UUID] = None,
    is_public: bool = False,
) -> QuestionBank:
    """Create a new question bank."""
    bank = QuestionBank(
        name=name,
        description=description,
        category=category,
        created_by=user_id,
        organization_id=organization_id,
        is_public=is_public,
    )
    db.add(bank)
    await db.flush()
    return bank


async def get_bank(db: AsyncSession, bank_id: uuid.UUID) -> Optional[QuestionBank]:
    """Get a question bank by ID."""
    result = await db.execute(select(QuestionBank).where(QuestionBank.id == bank_id))
    return result.scalar_one_or_none()


async def list_banks(
    db: AsyncSession,
    user_id: uuid.UUID,
    category: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
) -> Dict[str, Any]:
    """List question banks for a user."""
    query = select(QuestionBank).where(
        (QuestionBank.created_by == user_id) | (QuestionBank.is_public)
    )
    
    if category:
        query = query.where(QuestionBank.category == category)
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0
    
    # Paginate
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    banks = list(result.scalars().all())
    
    return {
        "items": banks,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": (total + page_size - 1) // page_size,
    }


async def add_question_to_bank(
    db: AsyncSession,
    bank_id: uuid.UUID,
    question_text: str,
    question_type: str,
    difficulty: str,
    reference_answer: Optional[str] = None,
    keywords: Optional[List[str]] = None,
    concepts: Optional[List[str]] = None,
    tags: Optional[List[str]] = None,
    source_interview_id: Optional[uuid.UUID] = None,
) -> BankQuestion:
    """Add a question to a bank."""
    question = BankQuestion(
        bank_id=bank_id,
        question_text=question_text,
        question_type=question_type,
        difficulty=difficulty,
        reference_answer=reference_answer,
        keywords=keywords,
        concepts=concepts,
        tags=tags or [],
        source_interview_id=source_interview_id,
    )
    db.add(question)
    
    # Update bank question count
    bank = await get_bank(db, bank_id)
    if bank:
        bank.question_count = (bank.question_count or 0) + 1
    
    await db.flush()
    return question


async def import_questions_from_interview(
    db: AsyncSession,
    bank_id: uuid.UUID,
    interview_id: uuid.UUID,
) -> List[BankQuestion]:
    """Import questions from an existing interview into a bank."""
    result = await db.execute(
        select(Question).where(Question.interview_id == interview_id)
    )
    questions = list(result.scalars().all())
    
    imported = []
    for q in questions:
        bank_question = BankQuestion(
            bank_id=bank_id,
            question_text=q.question_text,
            question_type=q.question_type,
            difficulty=q.difficulty,
            reference_answer=getattr(q, "reference_answer", None),
            keywords=getattr(q, "keywords", None),
            concepts=getattr(q, "concepts", None),
            tags=[],
            source_interview_id=interview_id,
        )
        db.add(bank_question)
        imported.append(bank_question)
    
    # Update bank question count
    bank = await get_bank(db, bank_id)
    if bank:
        bank.question_count = (bank.question_count or 0) + len(imported)
    
    await db.flush()
    return imported


async def generate_interview_from_bank(
    db: AsyncSession,
    bank_id: uuid.UUID,
    candidate_id: uuid.UUID,
    user_id: uuid.UUID,
    count: int = 10,
    difficulty: Optional[str] = None,
) -> uuid.UUID:
    """Generate an interview using questions from a bank."""
    from app.services.interview_service import create_interview
    from app.schemas.interview import InterviewCreate
    
    # Get questions from bank
    query = select(BankQuestion).where(BankQuestion.bank_id == bank_id)
    if difficulty:
        query = query.where(BankQuestion.difficulty == difficulty)
    query = query.order_by(func.random()).limit(count)
    
    result = await db.execute(query)
    bank_questions = list(result.scalars().all())
    
    if not bank_questions:
        raise ValueError("No questions found in bank matching criteria")
    
    # Create interview
    interview_data = InterviewCreate(
        candidate_id=str(candidate_id),
        difficulty_level=2,
        question_count=len(bank_questions),
    )
    interview = await create_interview(db, interview_data, user_id)
    
    # Add questions to interview
    for i, bq in enumerate(bank_questions):
        question = Question(
            interview_id=interview.id,
            question_text=bq.question_text,
            question_type=bq.question_type,
            difficulty=bq.difficulty,
            order_index=i,
        )
        db.add(question)
    
    await db.flush()
    return interview.id


async def delete_bank(db: AsyncSession, bank_id: uuid.UUID) -> bool:
    """Delete a question bank and its questions."""
    bank = await get_bank(db, bank_id)
    if not bank:
        return False
    
    # Delete all questions in the bank
    await db.execute(
        select(BankQuestion).where(BankQuestion.bank_id == bank_id)
    )
    
    await db.delete(bank)
    await db.flush()
    return True


async def get_bank_questions(
    db: AsyncSession,
    bank_id: uuid.UUID,
    page: int = 1,
    page_size: int = 20,
    difficulty: Optional[str] = None,
    question_type: Optional[str] = None,
) -> Dict[str, Any]:
    """Get questions from a bank with filtering."""
    query = select(BankQuestion).where(BankQuestion.bank_id == bank_id)
    
    if difficulty:
        query = query.where(BankQuestion.difficulty == difficulty)
    if question_type:
        query = query.where(BankQuestion.question_type == question_type)
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0
    
    # Paginate
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    questions = list(result.scalars().all())
    
    return {
        "items": questions,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": (total + page_size - 1) // page_size,
    }
