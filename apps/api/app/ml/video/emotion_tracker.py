"""Emotion timeline tracker with smoothing."""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List
from collections import Counter, deque

logger = logging.getLogger(__name__)


class EmotionTracker:
    def __init__(self, window_size: int = 5):
        self.window_size = window_size
        self.timeline: List[Dict[str, Any]] = []
        self._recent_emotions: deque = deque(maxlen=window_size)
        self._recent_confidence: deque = deque(maxlen=window_size)

    def add_snapshot(self, emotion_data: Dict[str, Any]) -> Dict[str, Any]:
        timestamp = datetime.now(timezone.utc)
        raw_emotion = emotion_data.get("dominant_emotion", "neutral")
        raw_confidence = emotion_data.get("confidence_score", 50.0)

        self._recent_emotions.append(raw_emotion)
        self._recent_confidence.append(raw_confidence)

        smoothed_emotion = self._smooth_emotion()
        smoothed_confidence = self._smooth_confidence()

        entry = {
            "timestamp": timestamp,
            "raw_emotion": raw_emotion,
            "smoothed_emotion": smoothed_emotion,
            "raw_confidence": raw_confidence,
            "smoothed_confidence": round(smoothed_confidence, 1),
            "face_detected": emotion_data.get("face_detected", False),
            "emotion_scores": emotion_data.get("emotion_scores", {}),
        }

        self.timeline.append(entry)
        return entry

    def _smooth_emotion(self) -> str:
        if not self._recent_emotions:
            return "neutral"
        counts = Counter(self._recent_emotions)
        return counts.most_common(1)[0][0]

    def _smooth_confidence(self) -> float:
        if not self._recent_confidence:
            return 50.0
        return sum(self._recent_confidence) / len(self._recent_confidence)

    def get_timeline(self) -> List[Dict[str, Any]]:
        return self.timeline

    def get_summary(self) -> Dict[str, Any]:
        if not self.timeline:
            return {"dominant_emotion": "neutral", "average_confidence": 50.0, "emotion_changes": 0, "face_detection_rate": 0.0}

        emotions = [e["smoothed_emotion"] for e in self.timeline]
        confidences = [e["smoothed_confidence"] for e in self.timeline]
        faces_detected = sum(1 for e in self.timeline if e.get("face_detected", False))
        changes = sum(1 for i in range(1, len(emotions)) if emotions[i] != emotions[i - 1])

        emotion_counts = Counter(emotions)
        dominant = emotion_counts.most_common(1)[0][0]

        return {
            "dominant_emotion": dominant,
            "emotion_distribution": dict(emotion_counts),
            "average_confidence": round(sum(confidences) / len(confidences), 1),
            "emotion_changes": changes,
            "face_detection_rate": round(faces_detected / len(self.timeline), 3),
            "total_snapshots": len(self.timeline),
            "first_emotion": emotions[0] if emotions else "neutral",
            "last_emotion": emotions[-1] if emotions else "neutral",
        }

    def get_confidence_over_time(self) -> List[Dict[str, Any]]:
        return [
            {
                "timestamp": e["timestamp"].isoformat() if hasattr(e["timestamp"], "isoformat") else str(e["timestamp"]),
                "confidence": e["smoothed_confidence"],
                "emotion": e["smoothed_emotion"],
            }
            for e in self.timeline
        ]

    def reset(self) -> None:
        self.timeline = []
        self._recent_emotions.clear()
        self._recent_confidence.clear()
