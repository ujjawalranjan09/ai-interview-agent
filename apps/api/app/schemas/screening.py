"""Screening schemas — request/response validation."""
from typing import List, Optional
import uuid

from pydantic import BaseModel, Field


class ScreeningRequest(BaseModel):
    job_description: str = Field(..., min_length=50)


class ScreeningResponse(BaseModel):
    id: str
    candidate_id: str
    score: float
    breakdown: dict
    strengths: list
    gaps: list
    recommendation: str
    created_at: Optional[str] = None


class RankRequest(BaseModel):
    job_description: str = Field(..., min_length=50)
    candidate_ids: List[uuid.UUID]


class RankResponse(BaseModel):
    rankings: List[ScreeningResponse]
