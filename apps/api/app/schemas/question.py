"""Question schemas."""

from pydantic import BaseModel, field_validator
from datetime import datetime
import uuid


class QuestionResponse(BaseModel):
    id: uuid.UUID
    question_text: str
    question_type: str
    difficulty: str
    order_index: int
    candidate_answer_text: str | None = None
    answer_score: float
    semantic_score: float
    keyword_score: float
    concept_score: float
    follow_up_of: uuid.UUID | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class AnswerSubmit(BaseModel):
    answer_text: str

    @field_validator("answer_text")
    @classmethod
    def sanitize_answer(cls, v: str) -> str:
        from app.core.validation import sanitize_string
        return sanitize_string(v)
