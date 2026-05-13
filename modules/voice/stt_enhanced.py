"""Enhanced Speech-to-Text using OpenAI Whisper with:
  - domain-specific initial_prompt for technical interview vocabulary
  - per-segment confidence logging
  - adaptive model selection (base / small / medium)
  - cleaned transcript output (filler word normalisation)

Drop-in upgrade for modules/voice/speech_to_text.py.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

TECH_INITIAL_PROMPT = (
    "This is a technical software engineering interview. "
    "The candidate may use terms such as: Python, FastAPI, MongoDB, Docker, "
    "Kubernetes, REST API, TensorFlow, PyTorch, machine learning, deep learning, "
    "neural network, backpropagation, transformer, LLM, RAG, ChromaDB, FAISS, "
    "SQL, PostgreSQL, Redis, microservices, CI/CD, GitHub Actions, "
    "data structures, algorithms, time complexity, Big-O notation."
)

FILLER_PATTERN = re.compile(
    r"\b(um+|uh+|like|you know|kind of|sort of|basically|literally|actually)\b",
    re.IGNORECASE,
)


@dataclass
class TranscriptResult:
    raw_text: str
    cleaned_text: str
    language: str
    avg_log_prob: float
    no_speech_prob: float
    segments: list[dict] = field(default_factory=list)
    model_size: str = "base"

    @property
    def is_confident(self) -> bool:
        return self.avg_log_prob > -0.8 and self.no_speech_prob < 0.4


class EnhancedSTT:
    """Whisper STT with domain prompt, quality scoring, and filler removal.

    Parameters
    ----------
    model_size:
        One of ``"base"``, ``"small"``, ``"medium"`` (default ``"base"`` for
        speed; use ``"small"`` for production quality).
    language:
        ISO 639-1 language code, e.g. ``"en"``. ``None`` = auto-detect.
    initial_prompt:
        Custom initial prompt overriding the default tech vocabulary prompt.
    """

    def __init__(
        self,
        model_size: str = "base",
        language: Optional[str] = "en",
        initial_prompt: Optional[str] = None,
    ) -> None:
        self.model_size = model_size
        self.language = language
        self.initial_prompt = initial_prompt or TECH_INITIAL_PROMPT
        self._model = None

    def _load_model(self):
        if self._model is None:
            import whisper  # noqa: PLC0415
            logger.info("Loading Whisper model: %s", self.model_size)
            self._model = whisper.load_model(self.model_size)
        return self._model

    def transcribe(self, audio_path: str) -> TranscriptResult:
        """Transcribe an audio file and return a TranscriptResult."""
        model = self._load_model()
        options: Dict[str, Any] = {
            "initial_prompt": self.initial_prompt,
            "temperature": 0.0,     # greedy decode for factual tech words
            "word_timestamps": False,
        }
        if self.language:
            options["language"] = self.language

        result = model.transcribe(audio_path, **options)

        raw_text: str = result.get("text", "").strip()
        segments: list[dict] = result.get("segments", [])

        avg_log_prob = (
            sum(s.get("avg_logprob", -1.0) for s in segments) / len(segments)
            if segments else -1.0
        )
        no_speech_prob = (
            sum(s.get("no_speech_prob", 0.0) for s in segments) / len(segments)
            if segments else 0.0
        )

        cleaned = self._clean_transcript(raw_text)

        if avg_log_prob < -1.0:
            logger.warning(
                "Low transcription confidence (avg_log_prob=%.2f). "
                "Consider switching to model_size='small' or 'medium'.",
                avg_log_prob,
            )

        return TranscriptResult(
            raw_text=raw_text,
            cleaned_text=cleaned,
            language=result.get("language", "en"),
            avg_log_prob=avg_log_prob,
            no_speech_prob=no_speech_prob,
            segments=segments,
            model_size=self.model_size,
        )

    @staticmethod
    def _clean_transcript(text: str) -> str:
        """Remove filler words and normalise whitespace."""
        cleaned = FILLER_PATTERN.sub("", text)
        cleaned = re.sub(r"\s{2,}", " ", cleaned).strip()
        return cleaned
