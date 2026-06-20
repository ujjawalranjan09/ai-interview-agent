"""Speech-to-text using faster-whisper."""

import logging
import tempfile
import os
from typing import Any, Dict

logger = logging.getLogger(__name__)

_model = None
_model_name = None


def _get_model():
    global _model, _model_name
    from app.core.config import settings
    if _model is None or _model_name != settings.WHISPER_MODEL:
        try:
            from faster_whisper import WhisperModel
            logger.info("Loading faster-whisper model: %s", settings.WHISPER_MODEL)
            _model = WhisperModel(settings.WHISPER_MODEL, device="cpu", compute_type="int8")
            _model_name = settings.WHISPER_MODEL
        except ImportError:
            logger.warning("faster-whisper not available")
            _model = False
            _model_name = settings.WHISPER_MODEL
        except Exception as e:
            logger.warning("faster-whisper model loading failed: %s", e)
            _model = False
            _model_name = settings.WHISPER_MODEL
    return _model if _model else None


def transcribe_audio(audio_bytes: bytes, filename: str = "audio.wav") -> Dict[str, Any]:
    model = _get_model()
    if not model:
        return {"text": "", "segments": [], "language": "en", "duration": 0.0, "error": "STT model unavailable"}

    suffix = os.path.splitext(filename)[1] or ".wav"
    tmp = None
    try:
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        tmp.write(audio_bytes)
        tmp.close()

        segments_gen, info = model.transcribe(tmp.name, fp16=False)

        segments = []
        full_text_parts = []
        for seg in segments_gen:
            segments.append({"start": round(seg.start, 2), "end": round(seg.end, 2), "text": seg.text.strip()})
            full_text_parts.append(seg.text.strip())

        text = " ".join(full_text_parts)
        duration = info.duration if info else 0.0
        language = info.language if info else "en"

        logger.info("Transcribed %d chars, %d segments", len(text), len(segments))
        return {"text": text, "segments": segments, "language": language, "duration": round(duration, 2)}

    except Exception as e:
        logger.error("Transcription failed: %s", e)
        return {"text": "", "segments": [], "language": "en", "duration": 0.0, "error": str(e)}
    finally:
        if tmp:
            try:
                os.unlink(tmp.name)
            except OSError:
                pass
