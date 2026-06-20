import uuid
import random
from datetime import datetime
from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import COPILOT_SUGGESTION_TEMPLATES
from app.models.copilot_session import CopilotSession


def select_suggestion_types(answer_score: float) -> list[str]:
    if answer_score < 50:
        types = ["rephrase", "encourage"]
    elif answer_score < 80:
        types = ["follow_up", "star_method"]
    else:
        types = ["probe_deeper", "strong_area"]
    types.append("gap_fill")
    return types


def render_suggestion(suggestion_type: str, context: dict) -> dict:
    template_data = COPILOT_SUGGESTION_TEMPLATES[suggestion_type]
    template = random.choice(template_data["templates"])
    filler = defaultdict(lambda: "this topic", context)
    rendered = template.format_map(filler)
    return {
        "id": uuid.uuid4().hex,
        "type": suggestion_type,
        "icon": template_data["icon"],
        "color": template_data["color"],
        "text": rendered,
        "created_at": datetime.utcnow().isoformat(),
    }


async def get_or_create_session(
    interview_id: uuid.UUID, interviewer_id: uuid.UUID, db: AsyncSession
) -> CopilotSession:
    result = await db.execute(
        select(CopilotSession).where(CopilotSession.interview_id == interview_id)
    )
    session = result.scalar_one_or_none()
    if not session:
        session = CopilotSession(
            interview_id=interview_id, interviewer_id=interviewer_id
        )
        db.add(session)
        await db.flush()
    return session


def log_suggestion(session: CopilotSession, suggestion: dict) -> None:
    if session.suggestions_log is None:
        session.suggestions_log = []
    session.suggestions_log.append(suggestion)


async def generate_suggestions(
    interview_id: uuid.UUID,
    current_question_text: str,
    answer_text: str,
    answer_score: float,
    candidate_skills: list[str],
    db: AsyncSession,
) -> list[dict]:
    types = select_suggestion_types(answer_score)
    suggestions = []
    for stype in types:
        context = {
            "topic": current_question_text[:50] if current_question_text else "this topic",
            "skill": candidate_skills[0] if candidate_skills else "this area",
            "concept": answer_text[:30] if answer_text else "your approach",
        }
        suggestion = render_suggestion(stype, context)
        suggestions.append(suggestion)
    return suggestions
