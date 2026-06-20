"""Coaching schemas."""

from pydantic import BaseModel
from datetime import datetime
import uuid


class CoachingPlanResponse(BaseModel):
    interview_id: uuid.UUID
    candidate_name: str = ""
    overall_score: float = 0.0
    strong_topics: list[str] = []
    weak_topics: list[str] = []
    topic_plans: list[dict] = []
    one_week_plan: str = ""
    one_month_plan: str = ""
    three_month_plan: str = ""
    coaching_advice: str = ""
    generated_at: datetime | None = None

    model_config = {"from_attributes": True}
