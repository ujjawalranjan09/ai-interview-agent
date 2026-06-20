"""PDF report generator using FPDF2."""

import logging
from datetime import datetime
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


def generate_pdf_report(
    candidate_name: str,
    interview_data: Dict[str, Any],
    questions: List[Dict[str, Any]],
    feedback: Dict[str, Any],
    metrics: Dict[str, Any],
) -> bytes:
    from fpdf import FPDF

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Page 1: Title + Score
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 24)
    pdf.cell(0, 15, "AI Interview Agent", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.set_font("Helvetica", "", 14)
    pdf.cell(0, 10, "Interview Performance Report", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(5)

    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, f"Candidate: {candidate_name}", new_x="LMARGIN", new_y="NEXT")
    date_str = interview_data.get("created_at", datetime.now())
    if hasattr(date_str, "strftime"):
        date_str = date_str.strftime("%Y-%m-%d %H:%M")
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, f"Date: {date_str}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)

    avg_score = metrics.get("average_score", 0)
    grade = metrics.get("overall_grade", "N/A")
    y = pdf.get_y()
    pdf.set_fill_color(52, 152, 219)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 16)
    pdf.rect(15, y, 180, 25, style="F")
    pdf.set_xy(15, y + 3)
    pdf.cell(90, 10, f"Overall Score: {avg_score:.1f}/100", align="C")
    pdf.set_xy(105, y + 3)
    pdf.cell(90, 10, f"Grade: {grade}", align="C")
    pdf.set_text_color(0, 0, 0)
    pdf.set_y(y + 30)

    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 10, "Key Metrics", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    for label, value in [
        ("Questions Answered", f"{metrics.get('questions_answered', 0)}/{metrics.get('total_questions', 0)}"),
        ("Average Score", f"{avg_score:.1f}/100"),
        ("Score Trend", metrics.get("score_trend", "N/A")),
        ("Dominant Emotion", metrics.get("dominant_emotion", "neutral")),
    ]:
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(60, 7, f"{label}:")
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(0, 7, str(value), new_x="LMARGIN", new_y="NEXT")

    # Page 2: Questions
    if questions:
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 14)
        pdf.set_fill_color(236, 240, 241)
        pdf.cell(0, 10, "Question-by-Question Performance", new_x="LMARGIN", new_y="NEXT", fill=True)
        pdf.ln(3)

        pdf.set_font("Helvetica", "B", 8)
        pdf.set_fill_color(52, 73, 94)
        pdf.set_text_color(255, 255, 255)
        col_widths = [10, 30, 25, 20, 20, 20, 65]
        headers = ["#", "Type", "Difficulty", "Score", "Semantic", "Keyword", "Question"]
        for header, width in zip(headers, col_widths):
            pdf.cell(width, 7, header, border=1, fill=True, align="C")
        pdf.ln()

        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Helvetica", "", 7)
        for i, q in enumerate(questions[:20]):
            fill = i % 2 == 0
            if fill:
                pdf.set_fill_color(245, 245, 245)
            q_text = q.get("question_text", "")[:60]
            if len(q.get("question_text", "")) > 60:
                q_text += "..."
            row = [str(i + 1), q.get("question_type", "?")[:10], q.get("difficulty", "?"),
                   f"{q.get('answer_score', 0):.0f}", f"{q.get('semantic_score', 0):.0f}",
                   f"{q.get('keyword_score', 0):.0f}", q_text]
            for val, width in zip(row, col_widths):
                pdf.cell(width, 6, val, border=1, fill=fill)
            pdf.ln()

    # Page 3: Feedback
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_fill_color(236, 240, 241)
    pdf.cell(0, 10, "Interview Feedback", new_x="LMARGIN", new_y="NEXT", fill=True)
    pdf.ln(3)

    for section, color in [("strengths", (39, 174, 96)), ("weaknesses", (231, 76, 60)), ("suggestions", (52, 152, 219))]:
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(*color)
        pdf.cell(0, 8, section.title(), new_x="LMARGIN", new_y="NEXT")
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Helvetica", "", 10)
        for item in feedback.get(section, []):
            pdf.cell(5, 6, "-")
            pdf.multi_cell(0, 6, item)
            pdf.ln(1)
        pdf.ln(3)

    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 8, "Overall Assessment", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "I", 10)
    pdf.multi_cell(0, 6, feedback.get("overall_assessment", "No assessment available."))

    return bytes(pdf.output())
