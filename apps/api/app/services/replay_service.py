"""Replay system — build timeline data for interview review."""

import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


def build_replay_data(
    questions: List[Dict[str, Any]],
    emotion_timeline: List[Dict[str, Any]],
    interview_data: Dict[str, Any],
) -> Dict[str, Any]:
    events = []
    start_time = interview_data.get("start_time")

    for q in questions:
        ts = q.get("created_at") or q.get("timestamp")
        elapsed = _elapsed_seconds(start_time, ts)
        events.append({
            "type": "question",
            "timestamp": elapsed,
            "data": {
                "question_text": q.get("question_text", ""),
                "question_type": q.get("question_type", ""),
                "difficulty": q.get("difficulty", ""),
                "answer_text": q.get("candidate_answer_text", ""),
                "answer_score": q.get("answer_score", 0),
                "audio_s3_key": q.get("answer_audio_s3_key", ""),
                "order": q.get("order_index", 0),
            },
        })

    for e in emotion_timeline:
        ts = e.get("timestamp")
        elapsed = _elapsed_seconds(start_time, ts)
        events.append({
            "type": "emotion",
            "timestamp": elapsed,
            "data": {
                "facial_emotion": e.get("facial_emotion", "neutral"),
                "confidence": e.get("combined_confidence", 50),
                "voice_pitch": e.get("voice_pitch", 0),
                "speaking_speed": e.get("speaking_speed", 0),
                "hesitation_detected": e.get("hesitation_detected", False),
            },
        })

    events.sort(key=lambda x: x.get("timestamp", 0))

    emotion_markers = [
        {"time": _elapsed_seconds(start_time, e.get("timestamp")), "emotion": e.get("facial_emotion", "neutral"), "confidence": e.get("combined_confidence", 50)}
        for e in emotion_timeline if e.get("timestamp")
    ]

    score_progression = [
        {"order": q.get("order_index", i), "score": q.get("answer_score", 0), "type": q.get("question_type", ""), "difficulty": q.get("difficulty", "")}
        for i, q in enumerate(questions)
    ]

    total_duration = 0
    if start_time and interview_data.get("end_time"):
        total_duration = _elapsed_seconds(start_time, interview_data["end_time"])

    return {
        "interview_id": str(interview_data.get("id", "")),
        "total_duration": round(total_duration, 1),
        "events": events,
        "emotion_markers": emotion_markers,
        "score_progression": score_progression,
    }


def _elapsed_seconds(start, end) -> float:
    if not start or not end:
        return 0.0
    try:
        if hasattr(start, "timestamp") and hasattr(end, "timestamp"):
            # Normalize both to the same timezone awareness
            from datetime import timezone
            if start.tzinfo is None and end.tzinfo is not None:
                start = start.replace(tzinfo=timezone.utc)
            elif start.tzinfo is not None and end.tzinfo is None:
                end = end.replace(tzinfo=timezone.utc)
            return round((end - start).total_seconds(), 1)
    except Exception:
        pass
    return 0.0
