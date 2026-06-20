"""Report schemas."""

from pydantic import BaseModel
from datetime import datetime
import uuid


class ReportResponse(BaseModel):
    interview_id: uuid.UUID
    metrics: dict = {}
    feedback: dict = {}
    chart_data: dict = {}
    pdf_url: str | None = None
    generated_at: datetime | None = None

    model_config = {"from_attributes": True}
