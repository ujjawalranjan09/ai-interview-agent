"""Question service — generation, submission, follow-up."""

import uuid
from typing import Any, Dict, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.question import Question


async def generate_interview_questions(
    db: AsyncSession,
    interview_id: uuid.UUID,
    skills: List[str],
    projects: List[str],
    count: int = 10,
    difficulty: str = "medium",
) -> List[Question]:
    from app.ml.questions.generator import generate_questions

    raw_questions = generate_questions(skills=skills, projects=projects, difficulty=difficulty, count=count)

    questions = []
    for i, q in enumerate(raw_questions):
        question = Question(
            interview_id=interview_id,
            question_text=q["question_text"],
            question_type=q.get("question_type", "technical"),
            difficulty=q.get("difficulty", difficulty),
            order_index=i,
        )
        db.add(question)
        questions.append(question)

    await db.flush()
    return questions


async def get_questions_for_interview(db: AsyncSession, interview_id: uuid.UUID) -> List[Question]:
    result = await db.execute(
        select(Question)
        .where(Question.interview_id == interview_id, Question.follow_up_of.is_(None))
        .order_by(Question.order_index)
    )
    return list(result.scalars().all())


async def get_question(db: AsyncSession, question_id: uuid.UUID) -> Question | None:
    result = await db.execute(select(Question).where(Question.id == question_id))
    return result.scalar_one_or_none()


async def submit_answer(db: AsyncSession, question_id: uuid.UUID, answer_text: str) -> Dict[str, Any]:
    question = await get_question(db, question_id)
    if not question:
        return {"error": "Question not found"}

    if question.candidate_answer_text:
        return {"error": "Question already answered"}

    from app.ml.evaluation.answer_evaluator import evaluate_answer
    from app.services.rubric_evaluator import evaluate_with_rubric
    
    # Basic evaluation
    evaluation = evaluate_answer(
        question=question.question_text,
        answer=answer_text,
        question_type=question.question_type,
    )
    
    # Rubric-based evaluation
    rubric_result = evaluate_with_rubric(
        question=question.question_text,
        answer=answer_text,
        question_type=question.question_type,
    )

    question.candidate_answer_text = answer_text
    question.answer_score = evaluation["total_score"]
    question.semantic_score = evaluation["semantic_score"]
    question.keyword_score = evaluation["keyword_score"]
    question.concept_score = evaluation["concept_score"]

    # Merge rubric results into evaluation
    evaluation["rubric_scores"] = rubric_result["rubric_scores"]
    evaluation["rubric_total"] = rubric_result["rubric_total"]
    evaluation["rubric_feedback"] = rubric_result["rubric_feedback"]
    evaluation["criteria_scores"] = rubric_result["criteria_scores"]

    await db.flush()
    return evaluation


async def request_followup(db: AsyncSession, question_id: uuid.UUID, answer_text: str, score: float) -> Question | None:
    question = await get_question(db, question_id)
    if not question:
        return None

    from app.ml.questions.follow_up import generate_followup
    followup_data = generate_followup(
        question=question.question_text,
        answer=answer_text,
        score=score,
        question_type=question.question_type,
    )

    # Get the max order_index for this interview
    result = await db.execute(
        select(Question.order_index)
        .where(Question.interview_id == question.interview_id)
        .order_by(Question.order_index.desc())
        .limit(1)
    )
    max_order = result.scalar() or 0

    followup = Question(
        interview_id=question.interview_id,
        question_text=followup_data["question_text"],
        question_type=followup_data["question_type"],
        difficulty=followup_data["difficulty"],
        order_index=max_order + 1,
        follow_up_of=question.id,
    )
    db.add(followup)
    await db.flush()
    return followup
