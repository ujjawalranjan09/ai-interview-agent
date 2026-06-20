"""Report endpoints."""

import logging
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.candidate import Candidate
from app.models.emotion_snapshot import EmotionSnapshot
from app.models.interview import Interview
from app.models.question import Question
from app.models.report import Report
from app.models.user import User
from app.schemas.report import ReportResponse

logger = logging.getLogger(__name__)

router = APIRouter(tags=["reports"])


async def _authorize_interview(db: AsyncSession, user: User, interview_id: uuid.UUID) -> Interview:
    result = await db.execute(select(Interview).where(Interview.id == interview_id))
    interview = result.scalar_one_or_none()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    if user.role == "admin":
        return interview
    # Candidate path: candidate.user_id == user.id
    c_result = await db.execute(select(Candidate).where(Candidate.id == interview.candidate_id))
    candidate = c_result.scalar_one_or_none()
    if candidate and candidate.user_id == user.id:
        return interview
    # Interviewer path
    if interview.interviewer_id and interview.interviewer_id == user.id:
        return interview
    raise HTTPException(status_code=403, detail="Not authorized to access this interview")


@router.get("/interviews/{interview_id}/report", response_model=ReportResponse, summary="Get interview report", description="Returns the generated report with metrics, feedback, and chart data for a completed interview.")
async def get_report(
    interview_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    await _authorize_interview(db, user, interview_id)
    result = await db.execute(select(Report).where(Report.interview_id == interview_id))
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found. POST /report/generate to create.")

    pdf_url = None
    if report.pdf_s3_key:
        try:
            from app.core.s3 import get_presigned_url
            pdf_url = get_presigned_url(report.pdf_s3_key)
        except Exception:
            pass

    return ReportResponse(
        interview_id=report.interview_id,
        metrics=report.chart_data.get("metrics", {}),
        feedback={
            "strengths": report.strengths or [],
            "weaknesses": report.weaknesses or [],
            "suggestions": report.suggestions or [],
            "overall_assessment": report.overall_assessment or "",
        },
        chart_data=report.chart_data.get("charts", {}),
        pdf_url=pdf_url,
        generated_at=report.generated_at,
    )


@router.get("/interviews/{interview_id}/report/pdf", summary="Download report as PDF", description="Downloads the interview report as a PDF file attachment.")
async def download_report_pdf(
    interview_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    await _authorize_interview(db, user, interview_id)
    result = await db.execute(select(Report).where(Report.interview_id == interview_id))
    report = result.scalar_one_or_none()
    if not report or not report.pdf_s3_key:
        raise HTTPException(status_code=404, detail="PDF report not found")

    from app.core.s3 import download_file
    pdf_bytes = download_file(report.pdf_s3_key)
    return Response(content=pdf_bytes, media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename=report_{interview_id}.pdf"})


@router.post("/interviews/{interview_id}/report/generate", response_model=ReportResponse, summary="Generate interview report", description="Generates a comprehensive report including performance metrics, AI feedback, and a PDF for a completed interview.")
async def generate_report(
    interview_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    interview = await _authorize_interview(db, user, interview_id)
    if interview.status != "completed":
        raise HTTPException(status_code=400, detail="Interview must be completed before generating a report")

    # Load questions
    q_result = await db.execute(select(Question).where(Question.interview_id == interview_id).order_by(Question.order_index))
    questions = list(q_result.scalars().all())
    answered = [q for q in questions if q.candidate_answer_text]
    if not answered:
        raise HTTPException(status_code=400, detail="Cannot generate report for interview with no answers")

    # Load emotion timeline
    e_result = await db.execute(select(EmotionSnapshot).where(EmotionSnapshot.interview_id == interview_id).order_by(EmotionSnapshot.timestamp))
    emotions = list(e_result.scalars().all())

    # Get candidate name
    c_result = await db.execute(select(Candidate).where(Candidate.id == interview.candidate_id))
    candidate = c_result.scalar_one_or_none()
    candidate_name = candidate.name if candidate else "Candidate"

    # Build data
    q_dicts = [{"question_text": q.question_text, "question_type": q.question_type, "difficulty": q.difficulty,
                "answer_score": q.answer_score, "semantic_score": q.semantic_score, "keyword_score": q.keyword_score,
                "concept_score": q.concept_score, "candidate_answer_text": q.candidate_answer_text,
                "order_index": q.order_index, "created_at": q.created_at}
               for q in questions]
    e_dicts = [{"facial_emotion": e.facial_emotion, "combined_confidence": e.combined_confidence,
                "voice_pitch": e.voice_pitch, "speaking_speed": e.speaking_speed,
                "hesitation_detected": e.hesitation_detected, "timestamp": e.timestamp}
               for e in emotions]

    # Calculate metrics
    from app.services.analytics_service import calculate_performance_metrics, build_chart_data
    metrics = calculate_performance_metrics(q_dicts, e_dicts)
    chart_data = build_chart_data(q_dicts, e_dicts, metrics)

    # Generate feedback
    from app.services.feedback_service import generate_feedback
    feedback = generate_feedback(candidate_name, q_dicts, e_dicts, metrics)

    # Generate PDF
    from app.services.report_service import generate_pdf_report
    interview_data = {"created_at": interview.created_at, "status": interview.status}
    pdf_bytes = generate_pdf_report(candidate_name, interview_data, q_dicts, feedback, metrics)

    # Upload to S3 (optional — gracefully skip if MinIO unavailable)
    s3_key = None
    try:
        from app.core.s3 import upload_file
        s3_key = f"reports/{interview_id}.pdf"
        upload_file(pdf_bytes, s3_key, "application/pdf")
    except Exception as exc:
        logger.warning("S3 upload skipped (MinIO may be offline): %s", str(exc)[:100])
        s3_key = None

    # Save report
    report_result = await db.execute(select(Report).where(Report.interview_id == interview_id))
    report = report_result.scalar_one_or_none()
    if report:
        report.pdf_s3_key = s3_key
        report.strengths = feedback.get("strengths", [])
        report.weaknesses = feedback.get("weaknesses", [])
        report.suggestions = feedback.get("suggestions", [])
        report.overall_assessment = feedback.get("overall_assessment", "")
        report.chart_data = {"metrics": metrics, "charts": chart_data}
    else:
        report = Report(
            interview_id=interview_id, pdf_s3_key=s3_key,
            strengths=feedback.get("strengths", []), weaknesses=feedback.get("weaknesses", []),
            suggestions=feedback.get("suggestions", []), overall_assessment=feedback.get("overall_assessment", ""),
            chart_data={"metrics": metrics, "charts": chart_data},
        )
        db.add(report)

    await db.commit()

    pdf_url = None
    if s3_key:
        try:
            from app.core.s3 import get_presigned_url
            pdf_url = get_presigned_url(s3_key)
        except Exception:
            pass

    return ReportResponse(
        interview_id=interview_id, metrics=metrics, feedback=feedback, chart_data=chart_data,
        pdf_url=pdf_url, generated_at=report.generated_at,
    )
