from pydantic import BaseModel, ConfigDict


class CopilotSessionResponse(BaseModel):
    id: str
    interview_id: str
    interviewer_id: str
    created_at: str
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "session-abc123",
                "interview_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                "interviewer_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
                "created_at": "2025-06-01T10:00:00Z",
            }
        },
    )


class SuggestionResponse(BaseModel):
    id: str
    type: str
    icon: str
    color: str
    text: str
    created_at: str


class SuggestionsResponse(BaseModel):
    suggestions: list[SuggestionResponse]


class DismissRequest(BaseModel):
    suggestion_id: str
