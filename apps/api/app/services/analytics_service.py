"""Performance metrics calculation engine."""

import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


def calculate_performance_metrics(
    questions: List[Dict[str, Any]],
    emotion_timeline: List[Dict[str, Any]] | None = None,
) -> Dict[str, Any]:
    metrics: Dict[str, Any] = {}

    scores = [q.get("answer_score", 0) for q in questions if q.get("candidate_answer_text")]
    if scores:
        metrics["average_score"] = round(sum(scores) / len(scores), 1)
        metrics["max_score"] = round(max(scores), 1)
        metrics["min_score"] = round(min(scores), 1)
        metrics["score_std"] = round(_std(scores), 1)
        metrics["questions_answered"] = len(scores)
    else:
        metrics["average_score"] = 0.0
        metrics["max_score"] = 0.0
        metrics["min_score"] = 0.0
        metrics["score_std"] = 0.0
        metrics["questions_answered"] = 0

    metrics["total_questions"] = len(questions)

    type_scores: Dict[str, List[float]] = {}
    for q in questions:
        qt = q.get("question_type", "technical")
        type_scores.setdefault(qt, []).append(q.get("answer_score", 0))
    metrics["scores_by_type"] = {
        qt: round(sum(s) / len(s), 1) if s else 0.0 for qt, s in type_scores.items()
    }

    diff_scores: Dict[str, List[float]] = {}
    for q in questions:
        d = q.get("difficulty", "medium")
        diff_scores.setdefault(d, []).append(q.get("answer_score", 0))
    metrics["scores_by_difficulty"] = {
        d: round(sum(s) / len(s), 1) if s else 0.0 for d, s in diff_scores.items()
    }

    if len(scores) >= 3:
        first_half = scores[: len(scores) // 2]
        second_half = scores[len(scores) // 2 :]
        diff = (sum(second_half) / len(second_half)) - (sum(first_half) / len(first_half))
        if diff > 5:
            metrics["score_trend"] = "improving"
        elif diff < -5:
            metrics["score_trend"] = "declining"
        else:
            metrics["score_trend"] = "stable"
        metrics["trend_magnitude"] = round(diff, 1)
    else:
        metrics["score_trend"] = "insufficient_data"
        metrics["trend_magnitude"] = 0.0

    metrics["average_semantic"] = round(_avg([q.get("semantic_score", 0) for q in questions]), 1)
    metrics["average_keyword"] = round(_avg([q.get("keyword_score", 0) for q in questions]), 1)
    metrics["average_concept"] = round(_avg([q.get("concept_score", 0) for q in questions]), 1)

    if emotion_timeline:
        emotions = [e.get("facial_emotion", "neutral") for e in emotion_timeline]
        confidences = [e.get("combined_confidence", 50) for e in emotion_timeline]
        from collections import Counter
        emotion_counts = Counter(emotions)
        metrics["dominant_emotion"] = emotion_counts.most_common(1)[0][0] if emotions else "neutral"
        metrics["emotion_distribution"] = dict(emotion_counts)
        metrics["average_confidence"] = round(sum(confidences) / len(confidences), 1) if confidences else 50.0
        metrics["emotion_stability"] = round(
            1.0 - (sum(1 for i in range(1, len(emotions)) if emotions[i] != emotions[i - 1]) / max(len(emotions) - 1, 1)),
            3,
        )
    else:
        metrics["dominant_emotion"] = "neutral"
        metrics["emotion_distribution"] = {}
        metrics["average_confidence"] = 50.0
        metrics["emotion_stability"] = 1.0

    metrics["overall_grade"] = _score_to_grade(metrics["average_score"])
    return metrics


def build_chart_data(
    questions: List[Dict[str, Any]],
    emotion_timeline: List[Dict[str, Any]] | None,
    metrics: Dict[str, Any],
) -> Dict[str, Any]:
    score_bar = [
        {"label": f"Q{i + 1}", "score": q.get("answer_score", 0), "type": q.get("question_type", "")}
        for i, q in enumerate(questions)
    ]

    scores = [q.get("answer_score", 0) for q in questions]
    rolling_avg = []
    for i in range(len(scores)):
        start = max(0, i - 2)
        rolling_avg.append(round(sum(scores[start : i + 1]) / (i - start + 1), 1))
    score_line = [
        {"label": f"Q{i + 1}", "score": s, "rolling_avg": r}
        for i, (s, r) in enumerate(zip(scores, rolling_avg))
    ]

    emotion_area = []
    if emotion_timeline:
        start_time = None
        for e in emotion_timeline:
            ts = e.get("timestamp")
            if start_time is None and ts:
                start_time = ts
            if ts and hasattr(ts, "timestamp"):
                elapsed = (ts - start_time).total_seconds() if start_time else 0
            else:
                elapsed = 0
            emotion_area.append({
                "time": round(elapsed, 1),
                "confidence": e.get("combined_confidence", 50),
                "emotion": e.get("facial_emotion", "neutral"),
            })

    skill_radar = [
        {"dimension": "Semantic", "value": metrics.get("average_semantic", 0)},
        {"dimension": "Keywords", "value": metrics.get("average_keyword", 0)},
        {"dimension": "Concepts", "value": metrics.get("average_concept", 0)},
        {"dimension": "Confidence", "value": metrics.get("average_confidence", 50)},
        {"dimension": "Fluency", "value": round(metrics.get("emotion_stability", 0.8) * 100, 1)},
    ]

    type_counts: Dict[str, Dict[str, Any]] = {}
    for q in questions:
        qt = q.get("question_type", "unknown")
        if qt not in type_counts:
            type_counts[qt] = {"type": qt, "count": 0, "scores": []}
        type_counts[qt]["count"] += 1
        type_counts[qt]["scores"].append(q.get("answer_score", 0))
    type_pie = [
        {"type": v["type"], "count": v["count"], "avg_score": round(sum(v["scores"]) / len(v["scores"]), 1) if v["scores"] else 0}
        for v in type_counts.values()
    ]

    from app.core.constants import DifficultyLevel
    difficulty_step = [
        {"label": f"Q{i + 1}", "difficulty": DifficultyLevel.LEVELS.get(q.get("difficulty", "medium"), 2), "score": q.get("answer_score", 0)}
        for i, q in enumerate(questions)
    ]

    comparison_grouped = [
        {"label": f"Q{i + 1}", "semantic": q.get("semantic_score", 0), "keyword": q.get("keyword_score", 0), "concept": q.get("concept_score", 0)}
        for i, q in enumerate(questions)
    ]

    return {
        "score_bar": score_bar,
        "score_line": score_line,
        "emotion_area": emotion_area,
        "skill_radar": skill_radar,
        "type_pie": type_pie,
        "difficulty_step": difficulty_step,
        "comparison_grouped": comparison_grouped,
    }


def _avg(values: list) -> float:
    return sum(values) / len(values) if values else 0.0


def _std(values: list) -> float:
    if len(values) < 2:
        return 0.0
    mean = sum(values) / len(values)
    variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
    return round(variance ** 0.5, 2)


def _score_to_grade(score: float) -> str:
    if score >= 90:
        return "A+"
    elif score >= 85:
        return "A"
    elif score >= 80:
        return "A-"
    elif score >= 75:
        return "B+"
    elif score >= 70:
        return "B"
    elif score >= 65:
        return "B-"
    elif score >= 60:
        return "C+"
    elif score >= 55:
        return "C"
    elif score >= 50:
        return "C-"
    elif score >= 40:
        return "D"
    return "F"
