"""DeepFace emotion classification from video frames."""

import logging
from typing import Any, Dict, List

import numpy as np

logger = logging.getLogger(__name__)

_deepface_loaded = None


def _ensure_deepface():
    global _deepface_loaded
    if _deepface_loaded is None:
        try:
            import deepface  # noqa: F401
            _deepface_loaded = True
        except (ImportError, Exception) as e:
            logger.warning("DeepFace not available: %s", e)
            _deepface_loaded = False
    return _deepface_loaded


def detect_emotion(frame: np.ndarray) -> Dict[str, Any]:
    if not _ensure_deepface():
        return {
            "dominant_emotion": "neutral",
            "emotion_scores": {"neutral": 1.0},
            "face_detected": False,
            "face_region": {},
            "confidence_score": 50.0,
            "fallback": True,
        }

    try:
        from deepface import DeepFace

        result = DeepFace.analyze(frame, actions=["emotion"], enforce_detection=False, silent=True)
        if isinstance(result, list):
            result = result[0]

        emotion_data = result.get("emotion", {})
        dominant = result.get("dominant_emotion", "neutral")
        face_region = result.get("region", {})

        total = sum(emotion_data.values()) if emotion_data else 1
        normalized_scores = {k: round(v / total, 4) if total > 0 else 0 for k, v in emotion_data.items()}

        confidence = _emotion_to_confidence(dominant, normalized_scores)

        return {
            "dominant_emotion": dominant,
            "emotion_scores": normalized_scores,
            "face_detected": bool(face_region and face_region.get("w", 0) > 0),
            "face_region": face_region,
            "confidence_score": round(confidence, 1),
        }
    except Exception as e:
        logger.warning("Emotion detection failed: %s", e)
        return {
            "dominant_emotion": "neutral",
            "emotion_scores": {},
            "face_detected": False,
            "face_region": {},
            "confidence_score": 50.0,
            "error": str(e),
        }


def _emotion_to_confidence(emotion: str, scores: Dict[str, float]) -> float:
    from app.core.constants import POSITIVE_EMOTIONS, NEGATIVE_EMOTIONS

    base_score = 50.0
    if emotion.lower() in POSITIVE_EMOTIONS:
        base_score += 25
    elif emotion.lower() in NEGATIVE_EMOTIONS:
        base_score -= 20

    if emotion.lower() in scores:
        detection_confidence = scores[emotion.lower()]
        base_score *= (0.5 + 0.5 * detection_confidence)

    return max(0.0, min(100.0, base_score))


def detect_emotions_batch(frames: List[np.ndarray]) -> List[Dict[str, Any]]:
    return [detect_emotion(frame) for frame in frames]


def get_emotion_summary(emotion_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not emotion_results:
        return {"dominant_emotion": "neutral", "face_detection_rate": 0.0}

    from collections import Counter

    emotions = [r.get("dominant_emotion", "neutral") for r in emotion_results]
    confidence_scores = [r.get("confidence_score", 50.0) for r in emotion_results]
    faces_detected = sum(1 for r in emotion_results if r.get("face_detected", False))

    emotion_counts = Counter(emotions)
    most_common_emotion = emotion_counts.most_common(1)[0][0]

    return {
        "dominant_emotion": most_common_emotion,
        "emotion_distribution": dict(emotion_counts),
        "average_confidence": round(sum(confidence_scores) / len(confidence_scores), 1),
        "face_detection_rate": round(faces_detected / len(emotion_results), 3),
        "total_frames": len(emotion_results),
    }
