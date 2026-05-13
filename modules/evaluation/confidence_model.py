"""Multimodal confidence model combining facial, voice-emotion, fluency, and text-sentiment signals.

This module replaces the old 3-signal formula (facial 0.5 / voice_tone 0.3 / fluency 0.2)
with a 4-signal weighted fusion that includes a text-sentiment channel.
Weights are read from app.config.CONFIDENCE_WEIGHTS and can be overridden per-call.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# ── Public API ────────────────────────────────────────────────────────────────

def calculate_confidence(
    facial_confidence: float = 50.0,
    voice_confidence: float = 50.0,
    fluency_score: float = 50.0,
    text_sentiment_score: float = 50.0,
    weights: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    """Calculate combined confidence score from multimodal signals.

    Formula (default weights from config):
        Total = 0.35×(Facial) + 0.30×(VoiceEmotion) + 0.20×(Fluency) + 0.15×(TextSentiment)

    Args:
        facial_confidence:    Facial emotion confidence (0-100).
        voice_confidence:     Speech-emotion model output (0-100).
        fluency_score:        Acoustic fluency score (0-100).
        text_sentiment_score: Text-level sentiment confidence (0-100).
        weights:              Optional weight dict to override config defaults.
                              Expected keys: facial, voice_emotion, fluency, text_sentiment.

    Returns:
        Dictionary with combined score, per-signal breakdown, and confidence level.
    """
    from app.config import CONFIDENCE_WEIGHTS

    w = weights if weights else CONFIDENCE_WEIGHTS

    facial_w = w.get("facial", 0.35)
    voice_w = w.get("voice_emotion", w.get("voice_tone", 0.30))  # accept legacy key
    fluency_w = w.get("fluency", 0.20)
    text_w = w.get("text_sentiment", 0.15)

    # Normalise in case weights don't sum to 1
    total_w = facial_w + voice_w + fluency_w + text_w
    if total_w > 0:
        facial_w /= total_w
        voice_w /= total_w
        fluency_w /= total_w
        text_w /= total_w

    combined = (
        facial_w * facial_confidence
        + voice_w * voice_confidence
        + fluency_w * fluency_score
        + text_w * text_sentiment_score
    )
    combined = max(0.0, min(100.0, combined))

    return {
        "combined_score": round(combined, 1),
        "facial_score": round(facial_confidence, 1),
        "voice_score": round(voice_confidence, 1),
        "fluency_score": round(fluency_score, 1),
        "text_sentiment_score": round(text_sentiment_score, 1),
        "weights_used": {
            "facial": round(facial_w, 3),
            "voice_emotion": round(voice_w, 3),
            "fluency": round(fluency_w, 3),
            "text_sentiment": round(text_w, 3),
        },
        "confidence_level": _score_to_level(combined),
    }


def calculate_fluency_score(
    speaking_speed: float,
    pause_ratio: float,
    hesitation_detected: bool,
    word_count: int = 0,
    duration: float = 0.0,
) -> float:
    """Calculate speech fluency score from acoustic features.

    Args:
        speaking_speed:       Speaking rate in words per minute.
        pause_ratio:          Fraction of audio that is silence (0-1).
        hesitation_detected:  Whether filler words / hesitations were detected.
        word_count:           Number of words spoken.
        duration:             Total audio duration in seconds.

    Returns:
        Fluency score (0-100).
    """
    score = 50.0

    # Speaking speed — ideal range 120-160 wpm
    if 120 <= speaking_speed <= 160:
        score += 20
    elif 100 <= speaking_speed <= 180:
        score += 10
    elif speaking_speed < 80 or speaking_speed > 200:
        score -= 15

    # Pause ratio — frequent pauses reduce fluency
    if pause_ratio < 0.2:
        score += 15
    elif pause_ratio < 0.4:
        score += 5
    elif pause_ratio > 0.6:
        score -= 20

    # Hesitations (um, uh, er, …)
    if hesitation_detected:
        score -= 15

    # Verify WPM from actual word_count / duration if available
    if duration > 0 and word_count > 0:
        actual_wpm = (word_count / duration) * 60
        if 100 <= actual_wpm <= 180:
            score += 10

    return max(0.0, min(100.0, score))


def aggregate_confidence_timeline(timeline: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Aggregate confidence scores over an interview timeline.

    Args:
        timeline: List of dicts from calculate_confidence().

    Returns:
        Dict with average, min, max, trend (improving / declining / stable).
    """
    if not timeline:
        return {"average": 50.0, "min": 50.0, "max": 50.0, "trend": "stable"}

    scores = [entry.get("combined_score", 50.0) for entry in timeline]
    avg = sum(scores) / len(scores)

    trend = "stable"
    if len(scores) >= 3:
        first_half = sum(scores[: len(scores) // 2]) / (len(scores) // 2)
        second_half = sum(scores[len(scores) // 2 :]) / (len(scores) - len(scores) // 2)
        diff = second_half - first_half
        if diff >= 5:
            trend = "improving"
        elif diff <= -5:
            trend = "declining"

    return {
        "average": round(avg, 1),
        "min": round(min(scores), 1),
        "max": round(max(scores), 1),
        "trend": trend,
        "data_points": len(scores),
    }


# ── Internal helpers ──────────────────────────────────────────────────────────

def _score_to_level(score: float) -> str:
    """Map a numeric score to a human-readable confidence level."""
    if score >= 80:
        return "very_confident"
    elif score >= 65:
        return "confident"
    elif score >= 50:
        return "moderate"
    elif score >= 35:
        return "uncertain"
    return "low_confidence"
