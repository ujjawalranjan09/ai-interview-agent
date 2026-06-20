"""Dynamic follow-up question generation."""

import logging
import random
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


def should_generate_followup(
    answer_score: float,
    follow_up_probability: float = 0.3,
    max_followups: int = 2,
    current_followups: int = 0,
) -> bool:
    if current_followups >= max_followups:
        return False
    if answer_score < 40:
        adjusted_prob = follow_up_probability * 1.5
    elif answer_score > 85:
        adjusted_prob = follow_up_probability * 1.2
    else:
        adjusted_prob = follow_up_probability
    return random.random() < min(adjusted_prob, 0.8)


def generate_followup(
    question: str, answer: str, score: float,
    skills: List[str] | None = None, question_type: str = "technical",
) -> Dict[str, Any]:
    try:
        return _generate_followup_llm(question, answer, score, question_type)
    except Exception as e:
        logger.warning("LLM follow-up failed, using templates: %s", e)
        return _generate_followup_template(question, answer, score, skills, question_type)


def _generate_followup_llm(question: str, answer: str, score: float, question_type: str) -> Dict[str, Any]:
    from app.core.config import settings
    from app.core.constants import FOLLOWUP_PROMPT

    if not settings.OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY not configured")

    import openai
    client = openai.OpenAI(api_key=settings.OPENAI_API_KEY, base_url=settings.OPENAI_BASE_URL or None)

    prompt = FOLLOWUP_PROMPT.format(question=question, answer=answer[:500], score=score)
    response = client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        messages=[
            {"role": "system", "content": "You are a technical interviewer. Generate a concise follow-up question."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.7, max_tokens=200,
    )

    text = (response.choices[0].message.content or "").strip().strip('"').strip("'")
    return {"question_text": text, "question_type": question_type, "difficulty": _infer_difficulty(score), "is_followup": True}


def _generate_followup_template(
    question: str, answer: str, score: float,
    skills: List[str] | None = None, question_type: str = "technical",
) -> Dict[str, Any]:
    difficulty = _infer_difficulty(score)
    if score < 40:
        templates = [
            "Could you elaborate a bit more on that? Perhaps walk me through a specific example.",
            "I'd like to understand better - can you explain that in simpler terms?",
            "Let me rephrase: can you describe a practical use case for what you just mentioned?",
            "That's a good start. Can you go deeper into how that actually works under the hood?",
        ]
    elif score > 85:
        templates = [
            "Great answer! Now, what would happen if the requirements changed significantly? How would you adapt?",
            "Excellent. Can you describe the potential pitfalls or edge cases with that approach?",
            "That's well explained. How would you handle scaling that solution to 10x the current load?",
            "Very thorough. What alternative approaches did you consider, and why did you choose this one?",
        ]
    else:
        templates = [
            "Can you walk me through the specific steps you'd take to implement that?",
            "What trade-offs did you consider when making that decision?",
            "How would you test or validate that approach?",
            "Can you give a concrete example from your experience?",
        ]

    text = random.choice(templates)
    if skills:
        for skill in skills:
            if skill.lower() in answer.lower():
                text += f" Especially in the context of {skill}."
                break

    return {"question_text": text, "question_type": question_type, "difficulty": difficulty, "is_followup": True}


def _infer_difficulty(score: float) -> str:
    if score >= 85:
        return "hard"
    elif score >= 60:
        return "medium"
    return "easy"
