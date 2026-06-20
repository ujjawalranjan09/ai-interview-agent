from pydantic import BaseModel


class OverviewResponse(BaseModel):
    total_interviews: int
    completed_interviews: int
    average_score: float
    total_candidates: int
    interviews_this_week: int
    top_skills: list[dict]

    model_config = {
        "json_schema_extra": {
            "example": {
                "total_interviews": 25,
                "completed_interviews": 18,
                "average_score": 72.5,
                "total_candidates": 20,
                "interviews_this_week": 3,
                "top_skills": [{"skill": "python", "count": 15}, {"skill": "sql", "count": 12}],
            }
        },
    }


class CandidateHistoryItem(BaseModel):
    interview_id: str
    date: str
    score: float
    status: str
    question_count: int


class CandidateHistoryResponse(BaseModel):
    items: list[CandidateHistoryItem]


class TrendResponse(BaseModel):
    weekly_scores: list[dict]
    skill_distribution: list[dict]
