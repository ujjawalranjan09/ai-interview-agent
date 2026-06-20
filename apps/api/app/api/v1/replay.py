"""Replay endpoints."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.candidate import Candidate
from app.models.emotion_snapshot import EmotionSnapshot
from app.models.interview import Interview
from app.models.question import Question
from app.models.user import User
from app.schemas.replay import ReplayResponse

router = APIRouter(tags=["replay"])


async def _authorize_interview(db: AsyncSession, user: User, interview_id: uuid.UUID) -> Interview:
    result = await db.execute(select(Interview).where(Interview.id == interview_id))
    interview = result.scalar_one_or_none()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    if user.role == "admin":
        return interview
    c_result = await db.execute(select(Candidate).where(Candidate.id == interview.candidate_id))
    candidate = c_result.scalar_one_or_none()
    if candidate and candidate.user_id == user.id:
        return interview
    if interview.interviewer_id and interview.interviewer_id == user.id:
        return interview
    raise HTTPException(status_code=403, detail="Not authorized to access this interview")


@router.get("/interviews/{interview_id}/replay", response_model=ReplayResponse, summary="Get interview replay", description="Returns time-sequenced question and emotion data to replay a completed interview session.")
async def get_replay(
    interview_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    interview = await _authorize_interview(db, user, interview_id)
    if interview.status != "completed":
        raise HTTPException(status_code=400, detail="Interview not completed yet")

    q_result = await db.execute(select(Question).where(Question.interview_id == interview_id).order_by(Question.order_index))
    questions = list(q_result.scalars().all())

    e_result = await db.execute(select(EmotionSnapshot).where(EmotionSnapshot.interview_id == interview_id).order_by(EmotionSnapshot.timestamp))
    emotions = list(e_result.scalars().all())

    q_dicts = [{"question_text": q.question_text, "question_type": q.question_type, "difficulty": q.difficulty,
                "answer_score": q.answer_score, "candidate_answer_text": q.candidate_answer_text,
                "answer_audio_s3_key": q.answer_audio_s3_key, "order_index": q.order_index, "created_at": q.created_at}
               for q in questions]
    e_dicts = [{"facial_emotion": e.facial_emotion, "combined_confidence": e.combined_confidence,
                "voice_pitch": e.voice_pitch, "speaking_speed": e.speaking_speed,
                "hesitation_detected": e.hesitation_detected, "timestamp": e.timestamp}
               for e in emotions]

    from app.services.replay_service import build_replay_data
    replay = build_replay_data(q_dicts, e_dicts, {"id": str(interview.id), "start_time": interview.start_time, "end_time": interview.end_time})

    return ReplayResponse(**replay)
