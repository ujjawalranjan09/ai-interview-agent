"""Audio upload and processing pipeline service."""

import logging
import uuid
from typing import Any, Dict

from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

MAX_AUDIO_SIZE = 25 * 1024 * 1024  # 25MB
ALLOWED_FORMATS = {".wav", ".mp3", ".m4a", ".webm", ".ogg"}


async def process_audio_answer(
    db: AsyncSession, question_id: uuid.UUID, audio_bytes: bytes, filename: str,
) -> Dict[str, Any]:
    # Validate
    if len(audio_bytes) > MAX_AUDIO_SIZE:
        return {"error": "Audio file too large (max 25MB)", "status": 413}

    import os
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_FORMATS:
        return {"error": f"Unsupported format. Allowed: {', '.join(ALLOWED_FORMATS)}", "status": 422}

    # Check if already answered
    from sqlalchemy import select
    from app.models.question import Question
    result = await db.execute(select(Question).where(Question.id == question_id))
    question = result.scalar_one_or_none()
    if not question:
        return {"error": "Question not found", "status": 404}
    if question.candidate_answer_text:
        return {"error": "Answer already submitted", "status": 409}

    # Upload audio to S3
    from app.core.s3 import upload_file
    s3_key = f"audio/{question_id}{ext}"

    # Try async (Celery) first
    try:
        from app.tasks import celery_app
        from app.tasks.transcription import transcribe_task
        import asyncio

        # Check if broker is reachable (non-blocking)
        await asyncio.get_event_loop().run_in_executor(
            None, lambda: celery_app.connection().ensure_connection(max_retries=1)
        )
        upload_file(audio_bytes, s3_key, f"audio/{ext.lstrip('.')}")
        question.answer_audio_s3_key = s3_key
        task = transcribe_task.delay(s3_key, str(question_id))
        await db.commit()
        return {"task_id": task.id, "status": "processing", "question_id": str(question_id)}
    except Exception as e:
        logger.warning("Celery unavailable, falling back to sync: %s", e)

    # Fallback: sync processing
    from app.ml.voice.transcription import transcribe_audio
    from app.ml.voice.emotion import analyze_voice_emotion
    from app.ml.evaluation.answer_evaluator import evaluate_answer

    transcription = transcribe_audio(audio_bytes, filename)
    text = transcription.get("text", "")

    emotion = analyze_voice_emotion(audio_bytes)

    question.candidate_answer_text = text

    evaluation = evaluate_answer(
        question=question.question_text,
        answer=text,
        question_type=question.question_type,
    )
    question.answer_score = evaluation["total_score"]
    question.semantic_score = evaluation["semantic_score"]
    question.keyword_score = evaluation["keyword_score"]
    question.concept_score = evaluation["concept_score"]

    await db.commit()

    return {
        "evaluation": evaluation,
        "transcription": text,
        "emotion": emotion,
        "status": "completed",
    }
