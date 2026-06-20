from pydantic import BaseModel, Field, field_validator

from app.core.validation import sanitize_string


class JDUploadRequest(BaseModel):
    jd_text: str = Field(..., min_length=50)

    @field_validator("jd_text")
    @classmethod
    def sanitize_jd(cls, v: str) -> str:
        return sanitize_string(v)


class JDMatchResponse(BaseModel):
    match_percentage: float
    matched_required: list[str]
    missing_required: list[str]
    matched_preferred: list[str]
    missing_preferred: list[str]

    model_config = {
        "json_schema_extra": {
            "example": {
                "match_percentage": 60.0,
                "matched_required": ["python", "sql"],
                "missing_required": ["docker"],
                "matched_preferred": ["react"],
                "missing_preferred": ["aws", "kubernetes"],
            }
        },
    }


class JDQuestionRequest(BaseModel):
    jd_text: str = Field(..., min_length=50)
    count: int = Field(default=5, ge=1, le=20)

    @field_validator("jd_text")
    @classmethod
    def sanitize_jd(cls, v: str) -> str:
        return sanitize_string(v)


class JDQuestionItem(BaseModel):
    question_text: str
    question_type: str
    difficulty: str
    target_skill: str


class JDQuestionResponse(BaseModel):
    questions: list[JDQuestionItem]
