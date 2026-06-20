"""Replay schemas."""

from pydantic import BaseModel


class ReplayResponse(BaseModel):
    interview_id: str
    total_duration: float = 0.0
    events: list[dict] = []
    emotion_markers: list[dict] = []
    score_progression: list[dict] = []
