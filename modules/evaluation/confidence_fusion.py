"""Multimodal confidence score fusion layer.

Architecture Improvement #1: replaces the old 3-signal formula with a
properly weighted 4-signal fusion that combines:

  facial_emotion   (DeepFace)                weight = 0.35
  speech_emotion   (SpeechBrain wav2vec2)     weight = 0.35
  acoustic_score   (librosa features)         weight = 0.15
  text_sentiment   (HF sentiment pipeline)    weight = 0.15

Emotion Agreement Bonus
-----------------------
If facial and speech emotion channels **agree** on the same high-level
state (positive / negative / neutral), a +5 bonus is added.
If they **conflict** (one says positive, other says negative), a -3
penalty is applied.  This pushes the score toward reality rather than
averaging away disagreement.

Confidence Timeline
-------------------
The ``ConfidenceTimeline`` class accumulates per-answer scores and
exposes a trend (improving / declining / stable) for the evaluator
and coaching modules.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# -----------------------------------------------------------------------
# Signal weights
# -----------------------------------------------------------------------
WEIGHT_FACIAL = 0.35
WEIGHT_SPEECH_EMOTION = 0.35
WEIGHT_ACOUSTIC = 0.15
WEIGHT_TEXT_SENTIMENT = 0.15

AGREEMENT_BONUS = 5.0
CONFLICT_PENALTY = -3.0

# Emotion → valence bucket mapping
_POSITIVE_EMOTIONS = {"happy", "excited", "confident", "joy", "positive"}
_NEGATIVE_EMOTIONS = {"angry", "sad", "fear", "frustrated", "fearful", "nervous", "negative"}


def _valence(emotion: str) -> str:
    e = emotion.lower()
    if e in _POSITIVE_EMOTIONS:
        return "positive"
    if e in _NEGATIVE_EMOTIONS:
        return "negative"
    return "neutral"


@dataclass
class FusionInput:
    """Container for all signals going into the fusion layer."""
    facial_score: float = 50.0        # 0-100 from DeepFace confidence
    facial_emotion: str = "neutral"   # raw DeepFace emotion label
    speech_emotion_score: float = 50.0  # 0-100 from SpeechBrain
    speech_emotion_label: str = "neutral"  # raw SpeechBrain label
    acoustic_score: float = 50.0      # 0-100 from librosa features
    text_sentiment_score: float = 50.0  # 0-100 from HF sentiment
    question_index: int = 0
    answer_text: str = ""


@dataclass
class FusionResult:
    """Output of the fusion layer for a single answer."""
    confidence_score: float           # final 0-100 weighted score
    facial_score: float
    speech_emotion_score: float
    acoustic_score: float
    text_sentiment_score: float
    facial_emotion: str
    speech_emotion_label: str
    agreement_adjustment: float       # +5, 0, or -3
    emotion_agreement: str            # "agree" | "conflict" | "neutral"
    question_index: int
    label: str = ""                   # "confident" | "moderate" | "nervous"

    def __post_init__(self):
        if self.confidence_score >= 70:
            self.label = "confident"
        elif self.confidence_score >= 45:
            self.label = "moderate"
        else:
            self.label = "nervous"


def compute_confidence(inp: FusionInput) -> FusionResult:
    """Compute the fused confidence score from all 4 signals."""
    raw = (
        WEIGHT_FACIAL          * inp.facial_score
        + WEIGHT_SPEECH_EMOTION * inp.speech_emotion_score
        + WEIGHT_ACOUSTIC       * inp.acoustic_score
        + WEIGHT_TEXT_SENTIMENT * inp.text_sentiment_score
    )

    # Emotion agreement bonus / penalty
    fv = _valence(inp.facial_emotion)
    sv = _valence(inp.speech_emotion_label)

    if fv == "neutral" or sv == "neutral":
        adjustment = 0.0
        agreement = "neutral"
    elif fv == sv:
        adjustment = AGREEMENT_BONUS
        agreement = "agree"
    else:
        adjustment = CONFLICT_PENALTY
        agreement = "conflict"

    final = max(0.0, min(100.0, raw + adjustment))

    logger.debug(
        "Fusion: facial=%.1f speech=%.1f acoustic=%.1f text=%.1f adj=%.1f -> %.1f",
        inp.facial_score, inp.speech_emotion_score,
        inp.acoustic_score, inp.text_sentiment_score,
        adjustment, final,
    )

    return FusionResult(
        confidence_score=round(final, 2),
        facial_score=inp.facial_score,
        speech_emotion_score=inp.speech_emotion_score,
        acoustic_score=inp.acoustic_score,
        text_sentiment_score=inp.text_sentiment_score,
        facial_emotion=inp.facial_emotion,
        speech_emotion_label=inp.speech_emotion_label,
        agreement_adjustment=adjustment,
        emotion_agreement=agreement,
        question_index=inp.question_index,
    )


# -----------------------------------------------------------------------
# Text sentiment helper (HuggingFace pipeline, lazy-loaded)
# -----------------------------------------------------------------------
_SENTIMENT_PIPE = None
_SENTIMENT_MODEL = "distilbert-base-uncased-finetuned-sst-2-english"


def _get_sentiment_pipeline():
    global _SENTIMENT_PIPE
    if _SENTIMENT_PIPE is None:
        from transformers import pipeline  # noqa: PLC0415
        logger.info("Loading sentiment pipeline: %s", _SENTIMENT_MODEL)
        _SENTIMENT_PIPE = pipeline(
            "sentiment-analysis",
            model=_SENTIMENT_MODEL,
            truncation=True,
            max_length=512,
        )
    return _SENTIMENT_PIPE


def score_answer_sentiment(text: str) -> float:
    """Return a 0-100 sentiment score for answer text (higher = more positive/confident)."""
    if not text.strip():
        return 50.0
    try:
        pipe = _get_sentiment_pipeline()
        result = pipe(text[:512])[0]
        score = result["score"]  # 0.0-1.0
        if result["label"] == "POSITIVE":
            return round(score * 100, 2)
        else:
            return round((1 - score) * 100, 2)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Sentiment scoring failed: %s", exc)
        return 50.0


# -----------------------------------------------------------------------
# Confidence Timeline
# -----------------------------------------------------------------------

@dataclass
class ConfidenceTimeline:
    """Accumulates per-answer confidence results for the full interview."""
    results: List[FusionResult] = field(default_factory=list)

    def add(self, result: FusionResult) -> None:
        self.results.append(result)

    @property
    def scores(self) -> List[float]:
        return [r.confidence_score for r in self.results]

    @property
    def average(self) -> float:
        return round(sum(self.scores) / len(self.scores), 2) if self.scores else 0.0

    @property
    def trend(self) -> str:
        """Return 'improving', 'declining', or 'stable' based on last 3 vs first 3."""
        if len(self.scores) < 4:
            return "stable"
        first = sum(self.scores[:3]) / 3
        last = sum(self.scores[-3:]) / 3
        diff = last - first
        if diff > 5:
            return "improving"
        if diff < -5:
            return "declining"
        return "stable"

    def summary(self) -> Dict[str, Any]:
        return {
            "total_answers": len(self.results),
            "average_confidence": self.average,
            "trend": self.trend,
            "scores": self.scores,
            "labels": [r.label for r in self.results],
            "agreement_counts": {
                "agree": sum(1 for r in self.results if r.emotion_agreement == "agree"),
                "conflict": sum(1 for r in self.results if r.emotion_agreement == "conflict"),
                "neutral": sum(1 for r in self.results if r.emotion_agreement == "neutral"),
            },
        }
