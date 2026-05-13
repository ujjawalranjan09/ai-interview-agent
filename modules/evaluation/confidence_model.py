"""Multimodal confidence model: 4-signal weighted fusion.

Updated to integrate SpeechBrain speech emotion signal alongside
the existing facial and fluency signals.

Weights (default):
  0.40 × facial confidence  (DeepFace)
  0.35 × speech emotion     (SpeechBrain wav2vec2 — NEW)
  0.15 × acoustic features  (librosa heuristics)
  0.10 × fluency            (pause ratio, speaking rate)
"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Updated 4-signal weights — speech_emotion replaces old voice_tone
DEFAULT_CONFIDENCE_WEIGHTS = {
    "facial": 0.40,
    "speech_emotion": 0.35,
    "acoustic": 0.15,
    "fluency": 0.10,
}


def calculate_confidence(
    facial_confidence: float = 50.0,
    speech_emotion_confidence: float = 50.0,
    acoustic_confidence: float = 50.0,
    fluency_score: float = 50.0,
    # Legacy parameter kept for backward compatibility
    voice_confidence: Optional[float] = None,
    weights: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    """Calculate combined confidence score from 4 multimodal signals.

    If voice_confidence is provided (legacy), it is used as acoustic_confidence
    and speech_emotion_confidence defaults to 50 (neutral).

    Args:
        facial_confidence: DeepFace facial emotion confidence (0-100).
        speech_emotion_confidence: SpeechBrain wav2vec2 confidence (0-100).
        acoustic_confidence: librosa acoustic heuristic score (0-100).
        fluency_score: Speech fluency score (0-100).
        voice_confidence: Legacy parameter — maps to acoustic_confidence.
        weights: Custom weight dict. Must have keys: facial, speech_emotion,
            acoustic, fluency. Must sum to 1.0.

    Returns:
        Dictionary with combined score and breakdown.
    """
    # Backward compatibility
    if voice_confidence is not None:
        acoustic_confidence = voice_confidence

    w = weights or DEFAULT_CONFIDENCE_WEIGHTS

    combined = (
        w["facial"] * facial_confidence
        + w["speech_emotion"] * speech_emotion_confidence
        + w["acoustic"] * acoustic_confidence
        + w["fluency"] * fluency_score
    )
    combined = max(0.0, min(100.0, combined))

    return {
        "combined_score": round(combined, 1),
        "facial_score": round(facial_confidence, 1),
        "speech_emotion_score": round(speech_emotion_confidence, 1),
        "acoustic_score": round(acoustic_confidence, 1),
        "fluency_score": round(fluency_score, 1),
        "weights_used": w,
        "confidence_level": _score_to_level(combined),
    }


def calculate_fluency_score(
    speaking_speed: float,
    pause_ratio: float,
    hesitation_detected: bool,
    word_count: int = 0,
    duration: float = 0.0,
) -> float:
    """Calculate speech fluency score from voice features.

    Args:
        speaking_speed: Speaking rate in words per minute.
        pause_ratio: Fraction of audio that is silence.
        hesitation_detected: Whether hesitations were detected.
        word_count: Number of words spoken.
        duration: Duration in seconds.

    Returns:
        Fluency score (0-100).
    """
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


def aggregate_confidence_timeline(timeline: list) -> Dict[str, Any]:
    """Aggregate confidence scores over an interview timeline."""
    if not timeline:
        return {"average": 50.0, "min": 50.0, "max": 50.0, "trend": "stable"}

    scores = [entry.get("combined_score", 50.0) for entry in timeline]
    avg = sum(scores) / len(scores)

    if len(scores) >= 3:
        first_half = scores[:len(scores) // 2]
        second_half = scores[len(scores) // 2:]
        diff = (sum(second_half) / len(second_half)) - (sum(first_half) / len(first_half))
        trend = "improving" if diff > 5 else ("declining" if diff < -5 else "stable")
    else:
        trend = "stable"

    return {
        "average": round(avg, 1),
        "min": round(min(scores), 1),
        "max": round(max(scores), 1),
        "trend": trend,
        "data_points": len(scores),
    }
