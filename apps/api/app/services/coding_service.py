"""Coding service — CRUD operations for coding questions and submissions."""

import uuid
from typing import Any, Dict, Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.coding_question import CodingQuestion, CodingSubmission


async def create_question(
    db: AsyncSession,
    title: str,
    description: str,
    difficulty: str,
    category: str,
    language: str = "python",
    starter_code: Optional[str] = None,
    solution: Optional[str] = None,
    test_cases: Optional[list] = None,
    constraints: Optional[str] = None,
    examples: Optional[list] = None,
    tags: Optional[list] = None,
    user_id: Optional[uuid.UUID] = None,
    organization_id: Optional[uuid.UUID] = None,
) -> CodingQuestion:
    """Create a new coding question."""
    question = CodingQuestion(
        title=title,
        description=description,
        difficulty=difficulty,
        category=category,
        language=language,
        starter_code=starter_code,
        solution=solution,
        test_cases=test_cases or [],
        constraints=constraints,
        examples=examples or [],
        tags=tags or [],
        created_by=user_id,
        organization_id=organization_id,
    )
    db.add(question)
    await db.flush()
    return question


async def get_question(db: AsyncSession, question_id: uuid.UUID) -> Optional[CodingQuestion]:
    """Get a coding question by ID."""
    result = await db.execute(select(CodingQuestion).where(CodingQuestion.id == question_id))
    return result.scalar_one_or_none()


async def list_questions(
    db: AsyncSession,
    difficulty: Optional[str] = None,
    category: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
) -> Dict[str, Any]:
    """List coding questions with filtering."""
    query = select(CodingQuestion)
    
    if difficulty:
        query = query.where(CodingQuestion.difficulty == difficulty)
    if category:
        query = query.where(CodingQuestion.category == category)
    
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


async def submit_code(
    db: AsyncSession,
    question_id: uuid.UUID,
    candidate_id: uuid.UUID,
    code: str,
    language: str = "python",
) -> Dict[str, Any]:
    """Submit code for a coding question."""
    from app.services.code_execution import execute_python_code, CodeExecutionError
    
    question = await get_question(db, question_id)
    if not question:
        raise ValueError("Question not found")
    
    # Execute the code
    try:
        result = execute_python_code(code, question.test_cases)
    except CodeExecutionError as e:
        result = {
            "success": False,
            "output": "",
            "error": str(e),
            "execution_time": 0,
            "test_results": [],
        }
    
    # Calculate score based on test results
    test_results = result.get("test_results", [])
    passed_count = sum(1 for t in test_results if t.get("passed", False))
    total_tests = len(test_results) if test_results else 1
    score = (passed_count / total_tests) * 100 if total_tests > 0 else 0
    
    # Create submission
    submission = CodingSubmission(
        question_id=question_id,
        candidate_id=candidate_id,
        code=code,
        language=language,
        output=result.get("output", ""),
        error=result.get("error"),
        test_results=test_results,
        score=score,
        execution_time=result.get("execution_time", 0),
        passed=score >= 80,  # Consider passed if 80% or more tests pass
    )
    db.add(submission)
    await db.flush()
    
    return {
        "submission_id": str(submission.id),
        "success": result.get("success", False),
        "output": result.get("output", ""),
        "error": result.get("error"),
        "test_results": test_results,
        "score": score,
        "passed": submission.passed,
        "execution_time": result.get("execution_time", 0),
    }


async def get_submissions(
    db: AsyncSession,
    question_id: Optional[uuid.UUID] = None,
    candidate_id: Optional[uuid.UUID] = None,
    page: int = 1,
    page_size: int = 20,
) -> Dict[str, Any]:
    """Get coding submissions."""
    query = select(CodingSubmission)
    
    if question_id:
        query = query.where(CodingSubmission.question_id == question_id)
    if candidate_id:
        query = query.where(CodingSubmission.candidate_id == candidate_id)
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0
    
    # Paginate
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    submissions = list(result.scalars().all())
    
    return {
        "items": submissions,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": (total + page_size - 1) // page_size,
    }


async def delete_question(db: AsyncSession, question_id: uuid.UUID) -> bool:
    """Delete a coding question."""
    question = await get_question(db, question_id)
    if not question:
        return False
    
    await db.delete(question)
    await db.flush()
    return True
