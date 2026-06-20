"""Celery task definitions — transcription pipeline."""

import logging

from app.tasks import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=10)
def transcribe_task(self, audio_s3_key: str, question_id: str):
    """Download audio from S3, transcribe, evaluate, update DB."""
    try:
        import uuid

        from app.core.s3 import download_file
        from app.ml.voice.transcription import transcribe_audio
        from app.ml.voice.emotion import analyze_voice_emotion

        logger.info("Starting transcription for question %s", question_id)

        audio_bytes = download_file(audio_s3_key)

        transcription = transcribe_audio(audio_bytes, audio_s3_key)
        text = transcription.get("text", "")

        emotion = analyze_voice_emotion(audio_bytes)

        import asyncio
        from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
        from app.core.config import settings

        async def _update():
            engine = create_async_engine(settings.DATABASE_URL)
            session_factory = async_sessionmaker(engine, expire_on_commit=False)
            async with session_factory() as db:
                from sqlalchemy import select
                from app.models.question import Question

                result = await db.execute(select(Question).where(Question.id == uuid.UUID(question_id)))
                question = result.scalar_one_or_none()
                if not question:
                    logger.error("Question %s not found", question_id)
                    return

                question.candidate_answer_text = text

                from app.ml.evaluation.answer_evaluator import evaluate_answer
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

                # Persist emotion snapshot
                from app.models.emotion_snapshot import EmotionSnapshot
                snapshot = EmotionSnapshot(
                    interview_id=question.interview_id,
                    question_id=question.id,
                    voice_emotion=emotion.get("emotion_label", "neutral"),
                    combined_confidence=emotion.get("confidence_score", 50.0),
                    voice_pitch=emotion.get("pitch_mean", 0.0),
                    speaking_speed=emotion.get("speaking_speed", 0.0),
                    hesitation_detected=emotion.get("hesitation_detected", False),
                    raw_data=emotion,
                )
                db.add(snapshot)
                await db.commit()

                logger.info("Question %s updated with transcription (%d chars)", question_id, len(text))

            await engine.dispose()

        asyncio.run(_update())

        return {
            "question_id": question_id,
            "text": text,
            "emotion": emotion,
            "status": "completed",
        }

    except Exception as exc:
        logger.error("Transcription task failed for question %s: %s", question_id, exc)
        try:
            self.retry(exc=exc)
        except self.MaxRetriesExceededError:
            logger.error("Max retries exceeded for question %s", question_id)
            error_msg = str(exc)
            try:
                import asyncio
                import uuid
                from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
                from app.core.config import settings

                async def _store_error():
                    engine = create_async_engine(settings.DATABASE_URL)
                    async with async_sessionmaker(engine, expire_on_commit=False)() as db:
                        from sqlalchemy import select
                        from app.models.question import Question
                        result = await db.execute(select(Question).where(Question.id == uuid.UUID(question_id)))
                        q = result.scalar_one_or_none()
                        if q:
                            q.candidate_answer_text = f"[Transcription failed: {error_msg}]"
                            await db.commit()
                    await engine.dispose()

                asyncio.run(_store_error())
            except Exception:
                pass

            return {"question_id": question_id, "status": "failed", "error": str(exc)}
