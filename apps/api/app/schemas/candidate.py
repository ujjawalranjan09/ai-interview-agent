"""Candidate schemas."""

from pydantic import BaseModel, EmailStr
from datetime import datetime
import uuid


class CandidateCreate(BaseModel):
    name: str
    email: EmailStr


class CandidateUpdate(BaseModel):
    name: str | None = None
    email: EmailStr | None = None


class CandidateResponse(BaseModel):
    id: uuid.UUID
    name: str
    email: str
    resume_s3_key: str | None = None
    extracted_skills: list[str] | None = []
    extracted_projects: list[str] | None = []
    created_at: datetime

    model_config = {"from_attributes": True}


class CandidateDetailResponse(CandidateResponse):
    skill_graph: dict | None = None
    metadata_: dict | None = None
