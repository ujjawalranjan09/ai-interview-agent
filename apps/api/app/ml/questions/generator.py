"""Question generator using OpenAI API with template fallback."""

import logging
import random
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def generate_questions(
    skills: List[str],
    projects: List[str],
    difficulty: str = "medium",
    count: int = 10,
    question_types: Optional[Dict[str, float]] = None,
) -> List[Dict[str, Any]]:
    if question_types is None:
        question_types = {"resume": 0.4, "technical": 0.4, "behavioral": 0.2}

    try:
        return _generate_with_openai(skills, projects, difficulty, count, question_types)
    except Exception as e:
        logger.warning("OpenAI generation failed, using templates: %s", e)
        return _generate_with_templates(skills, projects, difficulty, count, question_types)


def _generate_with_openai(
    skills: List[str], projects: List[str], difficulty: str, count: int,
    question_types: Dict[str, float],
) -> List[Dict[str, Any]]:
    from app.core.config import settings
    from app.core.constants import QUESTION_GENERATION_PROMPT

    if not settings.OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY not configured")

    import openai
    client = openai.OpenAI(api_key=settings.OPENAI_API_KEY, base_url=settings.OPENAI_BASE_URL or None)

    prompt = QUESTION_GENERATION_PROMPT.format(
        count=count,
        skills=", ".join(skills[:15]),
        projects=", ".join(projects[:5]),
        difficulty=difficulty,
        types=", ".join(f"{k} ({v * 100:.0f}%)" for k, v in question_types.items()),
    )

    response = client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        messages=[
            {"role": "system", "content": "You are an expert technical interviewer. Generate diverse, specific interview questions."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.7,
        max_tokens=2000,
    )

    content = response.choices[0].message.content or ""
    return _parse_llm_questions(content, difficulty)


def _parse_llm_questions(content: str, default_difficulty: str) -> List[Dict[str, Any]]:
    questions = []
    for line in content.strip().split("\n"):
        line = line.strip()
        if not line:
            continue
        if line.startswith("[") and "]" in line:
            bracket_end = line.index("]")
            q_type = line[1:bracket_end].strip().lower()
            q_text = line[bracket_end + 1:].strip().lstrip("0123456789.-) ")
            if q_text and q_type in ("resume", "technical", "behavioral"):
                questions.append({"question_text": q_text, "question_type": q_type, "difficulty": default_difficulty})
        else:
            cleaned = line.lstrip("0123456789.-) ")
            if cleaned and len(cleaned) > 10:
                questions.append({"question_text": cleaned, "question_type": "technical", "difficulty": default_difficulty})
    return questions


def _generate_with_templates(
    skills: List[str], projects: List[str], difficulty: str, count: int,
    question_types: Dict[str, float],
) -> List[Dict[str, Any]]:
    from app.core.constants import TECHNICAL_QUESTION_TEMPLATES, RESUME_QUESTION_TEMPLATES, BEHAVIORAL_QUESTIONS

    questions: List[Dict[str, Any]] = []
    type_counts = {}
    remaining = count
    for q_type, weight in question_types.items():
        tc = max(1, int(count * weight))
        type_counts[q_type] = min(tc, remaining)
        remaining -= type_counts[q_type]

    while sum(type_counts.values()) < count and type_counts:
        for q_type in type_counts:
            if sum(type_counts.values()) >= count:
                break
            type_counts[q_type] += 1

    resume_count = type_counts.get("resume", 0)
    if resume_count > 0 and (skills or projects):
        used = set()
        for _ in range(resume_count):
            template = _pick_unique(RESUME_QUESTION_TEMPLATES, used)
            if template:
                skill = random.choice(skills) if skills else "your primary skill"
                other_skill = random.choice(skills) if len(skills) > 1 else "another technology"
                project = random.choice(projects) if projects else "your most recent project"
                questions.append({"question_text": template.format(skill=skill, other_skill=other_skill, project=project), "question_type": "resume", "difficulty": difficulty})

    tech_templates = TECHNICAL_QUESTION_TEMPLATES.get(difficulty, TECHNICAL_QUESTION_TEMPLATES["medium"])
    tech_count = type_counts.get("technical", 0)
    if tech_count > 0 and skills:
        used = set()
        for _ in range(tech_count):
            template = _pick_unique(tech_templates, used)
            if template:
                skill = random.choice(skills)
                other_skill = random.choice(skills) if len(skills) > 1 else "databases"
                questions.append({"question_text": template.format(skill=skill, other_skill=other_skill), "question_type": "technical", "difficulty": difficulty})

    behavioral_count = type_counts.get("behavioral", 0)
    if behavioral_count > 0:
        used = set()
        for _ in range(behavioral_count):
            q = _pick_unique(BEHAVIORAL_QUESTIONS, used)
            if q:
                questions.append({"question_text": q, "question_type": "behavioral", "difficulty": "easy"})

    random.shuffle(questions)
    return questions[:count]


def _pick_unique(items: list, used: set) -> Optional[str]:
    available = [item for item in items if item not in used]
    if not available:
        available = items
    if not available:
        return None
    choice = random.choice(available)
    used.add(choice)
    return choice


def generate_introduction(name: str, skills: List[str], question_count: int) -> str:
    from app.core.constants import INTRODUCTION_TEMPLATE
    top_skills = ", ".join(skills[:3]) if skills else "your technical expertise"
    return INTRODUCTION_TEMPLATE.format(name=name, top_skills=top_skills, question_count=question_count)


def generate_closing(name: str, answered_count: int, avg_score: float) -> str:
    from app.core.constants import CLOSING_TEMPLATE
    return CLOSING_TEMPLATE.format(name=name, answered_count=answered_count, avg_score=avg_score)
