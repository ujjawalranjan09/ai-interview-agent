"""Question endpoints."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.question import QuestionResponse, AnswerSubmit
from app.services import question_service, audio_service

router = APIRouter(tags=["questions"])


@router.get("/interviews/{interview_id}/questions", response_model=list[QuestionResponse], summary="Get interview questions", description="Returns all questions associated with a specific interview.")
async def get_questions_for_interview(
    interview_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    return await question_service.get_questions_for_interview(db, interview_id)


@router.get("/questions/{question_id}", response_model=QuestionResponse, summary="Get a question", description="Returns details for a specific question by ID.")
async def get_question(
    question_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    question = await question_service.get_question(db, question_id)
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    return question


@router.post("/questions/{question_id}/answer", summary="Submit an answer", description="Submits a text answer for a question and triggers AI evaluation scoring.")
async def submit_answer(
    question_id: uuid.UUID,
    body: AnswerSubmit,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    result = await question_service.submit_answer(db, question_id, body.answer_text)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.post("/questions/{question_id}/followup", response_model=QuestionResponse, summary="Request a follow-up question", description="Generates a follow-up question based on the candidate's previous answer.")
async def request_followup(
    question_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    question = await question_service.get_question(db, question_id)
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    if not question.candidate_answer_text:
        raise HTTPException(status_code=400, detail="Question not yet answered")

    followup = await question_service.request_followup(
        db, question_id, question.candidate_answer_text, question.answer_score,
    )
    if not followup:
        raise HTTPException(status_code=500, detail="Failed to generate follow-up")
    return followup


@router.get("/questions/{question_id}/evaluation", summary="Get question evaluation", description="Returns the AI-generated evaluation scores for a specific question.")
async def get_evaluation(
    question_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    question = await question_service.get_question(db, question_id)
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    return {
        "total_score": question.answer_score,
        "semantic_score": question.semantic_score,
        "keyword_score": question.keyword_score,
        "concept_score": question.concept_score,
    }


@router.post("/questions/{question_id}/answer-audio", summary="Submit audio answer", description="Uploads an audio answer for a question and processes it for transcription and scoring.")
async def submit_audio_answer(
    question_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    file: UploadFile = File(...),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    audio_bytes = await file.read()
    result = await audio_service.process_audio_answer(db, question_id, audio_bytes, file.filename)
    status_code = result.get("status", 200)
    if status_code >= 400:
        raise HTTPException(status_code=status_code, detail=result.get("error", "Unknown error"))
    return result


@router.get("/questions/{question_id}/task-status", summary="Get task status", description="Checks the processing status of an audio answer submission.")
async def get_task_status(
    question_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    question = await question_service.get_question(db, question_id)
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    if question.candidate_answer_text:
        return {
            "status": "completed",
            "question_id": str(question_id),
            "has_answer": True,
        }
    return {
        "status": "processing",
        "question_id": str(question_id),
        "has_answer": False,
    }
