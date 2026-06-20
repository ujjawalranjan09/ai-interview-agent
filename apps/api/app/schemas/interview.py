"""Interview schemas."""

from pydantic import BaseModel, field_validator
from datetime import datetime
import uuid


class InterviewCreate(BaseModel):
    candidate_id: uuid.UUID
    question_count: int = 10
    difficulty_level: int = 2
    config: dict | None = None


class InterviewUpdate(BaseModel):
    status: str | None = None
    difficulty_level: int | None = None
    config: dict | None = None


class InterviewResponse(BaseModel):
    id: uuid.UUID
    candidate_id: uuid.UUID
    interviewer_id: uuid.UUID | None = None
    status: str
    difficulty_level: int
    question_count: int
    questions_answered: int
    total_score: float
    start_time: datetime | None = None
    end_time: datetime | None = None
    created_at: datetime

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                "candidate_id": "1a2b3c4d-5e6f-7890-abcd-ef1234567890",
                "interviewer_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
                "status": "in_progress",
                "difficulty_level": 2,
                "question_count": 10,
                "questions_answered": 5,
                "total_score": 78.5,
                "start_time": "2025-06-01T10:00:00Z",
                "end_time": None,
                "created_at": "2025-06-01T09:30:00Z",
            }
        },
    }


class InterviewDetailResponse(InterviewResponse):
    config: dict | None = None


class ShareResponse(BaseModel):
    share_token: str
    share_url: str


class JoinInterviewResponse(BaseModel):
    id: str
    candidate_name: str
    question_count: int
    difficulty_level: str
    status: str
    first_question: dict | None = None


class JoinAnswerRequest(BaseModel):
    question_id: str
    answer_text: str

    @field_validator("answer_text")
    @classmethod
    def sanitize_answer(cls, v: str) -> str:
        from app.core.validation import sanitize_string
        return sanitize_string(v)


class JoinAnswerResponse(BaseModel):
    next_question: dict | None = None
    score: float | None = None
    completed: bool = False
