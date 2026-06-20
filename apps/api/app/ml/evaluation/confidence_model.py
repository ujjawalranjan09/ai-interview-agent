"""Multimodal confidence model — 4-signal weighted fusion."""

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


def calculate_confidence(
    facial_confidence: float = 50.0,
    voice_confidence: float = 50.0,
    fluency_score: float = 50.0,
    text_sentiment_score: float = 50.0,
    weights: Dict[str, float] | None = None,
) -> Dict[str, Any]:

    w = weights or {"facial": 0.35, "voice_emotion": 0.30, "fluency": 0.20, "text_sentiment": 0.15}

    facial_w = w.get("facial", 0.35)
    voice_w = w.get("voice_emotion", w.get("voice_tone", 0.30))
    fluency_w = w.get("fluency", 0.20)
    text_w = w.get("text_sentiment", 0.15)

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
        "confidence_level": _score_to_level(combined),
    }


def calculate_fluency_score(
    speaking_speed: float,
    pause_ratio: float,
    hesitation_detected: bool,
    word_count: int = 0,
    duration: float = 0.0,
) -> float:
    score = 50.0
    if 120 <= speaking_speed <= 160:
        score += 20
    elif 100 <= speaking_speed <= 180:
        score += 10
    elif speaking_speed < 80 or speaking_speed > 200:
        score -= 15

    if pause_ratio < 0.2:
        score += 15
    elif pause_ratio < 0.4:
        score += 5
    elif pause_ratio > 0.6:
        score -= 20

    if hesitation_detected:
        score -= 15

    if duration > 0 and word_count > 0:
        actual_wpm = (word_count / duration) * 60
        if 100 <= actual_wpm <= 180:
            score += 10

    return max(0.0, min(100.0, score))


def _score_to_level(score: float) -> str:
    if score >= 80:
        return "very_confident"
    elif score >= 65:
        return "confident"
    elif score >= 50:
        return "moderate"
    elif score >= 35:
        return "uncertain"
    return "low_confidence"
