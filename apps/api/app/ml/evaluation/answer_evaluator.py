"""Answer evaluation orchestrator — composite scoring."""

import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


def evaluate_answer(
    question: str,
    answer: str,
    reference_answer: str = "",
    keywords: List[str] | None = None,
    concepts: List[str] | None = None,
    question_type: str = "technical",
) -> Dict[str, Any]:

    if not answer or not answer.strip():
        return {
            "total_score": 0.0,
            "semantic_score": 0.0,
            "keyword_score": 0.0,
            "concept_score": 0.0,
            "modifiers": {},
            "feedback": "No answer provided.",
        }

    semantic_score = _calculate_semantic_score(question, answer, reference_answer)
    keyword_score = _calculate_keyword_score(answer, keywords or [])
    concept_score = _calculate_concept_score(answer, concepts or [])
    modifiers = _calculate_modifiers(answer)

    weights = {"semantic": 0.4, "keywords": 0.3, "concepts": 0.3}
    total = (
        weights["semantic"] * semantic_score
        + weights["keywords"] * keyword_score
        + weights["concepts"] * concept_score
    )
    total += modifiers.get("total_modifier", 0.0)
    total = max(0.0, min(100.0, total))

    feedback = _generate_feedback(total, semantic_score, keyword_score, concept_score)

    return {
        "total_score": round(total, 1),
        "semantic_score": round(semantic_score, 1),
        "keyword_score": round(keyword_score, 1),
        "concept_score": round(concept_score, 1),
        "modifiers": modifiers,
        "feedback": feedback,
    }


def _calculate_semantic_score(question: str, answer: str, reference: str) -> float:
    from app.ml.evaluation.semantic_scorer import compute_similarity
    if reference:
        return compute_similarity(answer, reference) * 100
    return compute_similarity(question, answer) * 100


def _calculate_keyword_score(answer: str, keywords: List[str]) -> float:
    if not keywords:
        wc = len(answer.split())
        if wc < 10:
            return 20.0
        elif wc < 30:
            return 50.0
        return 60.0
    answer_lower = answer.lower()
    matched = sum(1 for kw in keywords if kw.lower() in answer_lower)
    return (matched / len(keywords)) * 100


def _calculate_concept_score(answer: str, concepts: List[str]) -> float:
    if not concepts:
        score = 40.0
        wc = len(answer.split())
        if wc > 50:
            score += 20
        if wc > 100:
            score += 10
        indicators = [
            "because", "therefore", "however", "specifically",
            "for example", "such as", "trade-off", "advantage",
            "approach", "implementation", "architecture", "design pattern",
        ]
        depth_count = sum(1 for ind in indicators if ind in answer.lower())
        score += min(30, depth_count * 5)
        return min(100.0, score)
    answer_lower = answer.lower()
    covered = sum(1 for c in concepts if c.lower() in answer_lower)
    return (covered / len(concepts)) * 100


def _calculate_modifiers(answer: str) -> Dict[str, Any]:
    total_mod = 0.0
    details: Dict[str, Any] = {}
    wc = len(answer.split())

    if wc < 5:
        length_mod = -15.0
    elif wc < 15:
        length_mod = -5.0
    elif wc > 200:
        length_mod = 5.0
    else:
        length_mod = 0.0
    total_mod += length_mod
    details["length_modifier"] = length_mod

    structure_indicators = ["1.", "2.", "first", "second", "finally", "step"]
    structure_count = sum(1 for ind in structure_indicators if ind in answer.lower())
    structure_mod = 5.0 if structure_count >= 2 else 0.0
    total_mod += structure_mod
    details["structure_modifier"] = structure_mod

    fillers = ["um", "uh", "like", "you know", "basically", "i mean"]
    filler_count = sum(answer.lower().count(f) for f in fillers)
    filler_ratio = filler_count / max(wc, 1)
    if filler_ratio > 0.1:
        hesitation_mod = -10.0
    elif filler_ratio > 0.05:
        hesitation_mod = -5.0
    else:
        hesitation_mod = 0.0
    total_mod += hesitation_mod
    details["hesitation_modifier"] = hesitation_mod

    details["total_modifier"] = round(total_mod, 1)
    return details


def _generate_feedback(total: float, semantic: float, keyword: float, concept: float) -> str:
    parts = []
    if total >= 85:
        parts.append("Excellent answer!")
    elif total >= 70:
        parts.append("Good answer.")
    elif total >= 55:
        parts.append("Acceptable answer.")
    elif total >= 40:
        parts.append("Below average answer.")
    else:
        parts.append("Needs improvement.")
    if keyword < 40:
        parts.append("Consider using more relevant technical terms.")
    if concept < 40:
        parts.append("Try to cover more key concepts in your answer.")
    if semantic < 40:
        parts.append("Your answer could be more relevant to the question.")
    return " ".join(parts)
