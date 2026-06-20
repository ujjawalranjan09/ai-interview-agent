"""Development-only API endpoints."""
from fastapi import APIRouter, HTTPException
from app.core.config import settings
from app.services.email_templates import render_template, list_templates

router = APIRouter(prefix="/dev", tags=["dev"])


@router.get("/email-preview/{template_name}")
async def preview_email(template_name: str):
    if not settings.ENVIRONMENT == "development":
        raise HTTPException(status_code=404, detail="Not found")

    templates = list_templates()
    if template_name not in templates:
        raise HTTPException(status_code=404, detail=f"Unknown template. Available: {', '.join(templates)}")

    variables = {
        "candidate_name": "Jane Doe",
        "interviewer_name": "John Smith",
        "company_name": "Acme Corp",
        "action_url": "https://example.com/join/abc123",
        "duration": "60",
        "interview_date": "July 15, 2026 at 2:00 PM",
        "score": "85.5",
        "question_count": "10",
        "areas_count": "3",
    }

    subject, html, text = render_template(template_name, variables)
    return {"subject": subject, "html": html, "text": text}
