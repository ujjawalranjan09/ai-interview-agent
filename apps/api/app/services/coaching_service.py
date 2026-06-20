"""Coaching plan generator with resource recommender."""

import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

# Curated resource database (top entries from old resource_recommender.py)
_RESOURCES: Dict[str, List[Dict[str, Any]]] = {
    "python": [{"title": "Python Official Tutorial", "type": "article", "url": "https://docs.python.org/3/tutorial/", "difficulty": "beginner"}, {"title": "Automate the Boring Stuff", "type": "book", "url": "https://automatetheboringstuff.com/", "difficulty": "beginner"}],
    "javascript": [{"title": "JavaScript.info", "type": "article", "url": "https://javascript.info/", "difficulty": "beginner"}, {"title": "Eloquent JavaScript", "type": "book", "url": "https://eloquentjavascript.net/", "difficulty": "intermediate"}],
    "react": [{"title": "React Official Tutorial", "type": "article", "url": "https://react.dev/learn", "difficulty": "beginner"}, {"title": "React - The Complete Guide", "type": "course", "url": "https://www.udemy.com/course/react-the-complete-guide-incl-redux/", "difficulty": "intermediate"}],
    "sql": [{"title": "SQLBolt", "type": "article", "url": "https://sqlbolt.com/", "difficulty": "beginner"}, {"title": "Mode SQL Tutorial", "type": "article", "url": "https://mode.com/sql-tutorial/", "difficulty": "intermediate"}],
    "docker": [{"title": "Docker Official Getting Started", "type": "article", "url": "https://docs.docker.com/get-started/", "difficulty": "beginner"}],
    "machine learning": [{"title": "Andrew Ng's ML Course", "type": "course", "url": "https://www.coursera.org/learn/machine-learning", "difficulty": "beginner"}, {"title": "Fast.ai Practical Deep Learning", "type": "course", "url": "https://course.fast.ai/", "difficulty": "intermediate"}],
    "system design": [{"title": "System Design Primer", "type": "article", "url": "https://github.com/donnemartin/system-design-primer", "difficulty": "intermediate"}],
    "algorithms": [{"title": "LeetCode", "type": "practice", "url": "https://leetcode.com/", "difficulty": "intermediate"}, {"title": "NeetCode Roadmap", "type": "article", "url": "https://neetcode.io/roadmap", "difficulty": "intermediate"}],
    "data structures": [{"title": "Visualgo", "type": "article", "url": "https://visualgo.net/", "difficulty": "beginner"}],
    "leadership": [{"title": "The Making of a Manager", "type": "book", "url": "", "difficulty": "intermediate"}],
    "communication": [{"title": "Crucial Conversations", "type": "book", "url": "", "difficulty": "intermediate"}],
    "problem solving": [{"title": "Cracking the Coding Interview", "type": "book", "url": "", "difficulty": "intermediate"}],
}


def recommend_resources(topic: str, level: str = "intermediate", max_results: int = 4) -> List[Dict[str, Any]]:
    topic_lower = topic.lower()
    for key, resources in _RESOURCES.items():
        if key in topic_lower or topic_lower in key:
            return resources[:max_results]
    return [{"title": f"Practice {topic} problems on LeetCode", "type": "practice", "url": "https://leetcode.com/", "difficulty": level}]


def generate_coaching_plan(
    candidate_name: str,
    question_results: List[Dict[str, Any]],
    overall_score: float,
) -> Dict[str, Any]:
    weak_areas = _extract_weak_areas(question_results)
    strong_areas = _extract_strong_areas(question_results)

    topic_plans = []
    for area in weak_areas[:5]:
        topic = area["topic"]
        score = area["score"]
        level = "beginner" if score < 40 else "intermediate"
        target = "intermediate" if level == "beginner" else "advanced"
        resources = recommend_resources(topic, level)
        topic_plans.append({
            "topic": topic, "current_level": level, "target_level": target,
            "gap_description": area.get("description", f"Scored {score:.0f}/100"),
            "resources": resources,
            "practice_exercises": _generate_exercises(topic, level),
            "estimated_time": "2-4 weeks" if level == "beginner" else "4-8 weeks",
        })

    return {
        "candidate_name": candidate_name,
        "overall_score": overall_score,
        "strong_topics": strong_areas,
        "weak_topics": [t["topic"] for t in topic_plans],
        "topic_plans": topic_plans,
        "one_week_plan": _one_week_plan(topic_plans),
        "one_month_plan": _one_month_plan(topic_plans),
        "three_month_plan": _three_month_plan(topic_plans),
        "coaching_advice": _generate_advice(candidate_name, overall_score, topic_plans, strong_areas),
    }


def _extract_weak_areas(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    skill_scores: Dict[str, List[float]] = {}
    for r in results:
        skill = r.get("target_skill") or r.get("question_type", "general")
        skill_scores.setdefault(skill, []).append(r.get("answer_score", 0))
    weak = [{"topic": s, "score": sum(sc) / len(sc), "description": f"Avg {sum(sc)/len(sc):.0f}/100 across {len(sc)} questions"} for s, sc in skill_scores.items() if sum(sc) / len(sc) < 65]
    weak.sort(key=lambda x: x["score"])
    return weak[:8]


def _extract_strong_areas(results: List[Dict[str, Any]]) -> List[str]:
    skill_scores: Dict[str, List[float]] = {}
    for r in results:
        skill = r.get("target_skill") or r.get("question_type", "general")
        skill_scores.setdefault(skill, []).append(r.get("answer_score", 0))
    return sorted(s for s, sc in skill_scores.items() if sum(sc) / len(sc) >= 75)


def _generate_exercises(topic: str, level: str) -> List[str]:
    if level == "beginner":
        return [f"Complete 5 {topic} tutorials", f"Build a small project using {topic}", f"Read the {topic} documentation"]
    return [f"Solve 10 {topic} problems on LeetCode", f"Build a real-world app with {topic}", f"Contribute to an open-source {topic} project"]


def _one_week_plan(topics: List[Dict[str, Any]]) -> str:
    if not topics:
        return "No weak areas — maintain skills with regular practice."
    lines = ["**1-Week Improvement Sprint**\n"]
    for i, t in enumerate(topics[:2], 1):
        lines.append(f"**Days {(i-1)*3+1}-{i*3}: {t['topic']}**")
        lines.append(f"- Level: {t['current_level']} → {t['target_level']}")
        if t["resources"]:
            lines.append(f"- Start with: {t['resources'][0]['title']}")
        lines.append("")
    lines.append("**Days 6-7: Review & Practice**\n- Review what you learned\n- Take a practice interview")
    return "\n".join(lines)


def _one_month_plan(topics: List[Dict[str, Any]]) -> str:
    if not topics:
        return "No weak areas — continue regular practice."
    lines = ["**1-Month Improvement Plan**\n"]
    for i, t in enumerate(topics[:4], 1):
        lines.append(f"**Week {i}: {t['topic']}**")
        lines.append(f"- Current: {t['current_level']} | Target: {t['target_level']}")
        for r in t["resources"][:2]:
            lines.append(f"- {r['title']} ({r['type']})")
        lines.append("")
    return "\n".join(lines)


def _three_month_plan(topics: List[Dict[str, Any]]) -> str:
    if not topics:
        return "No weak areas — focus on advanced topics and system design."
    lines = ["**3-Month Comprehensive Roadmap**\n"]
    lines.append("**Month 1: Foundation**")
    for t in topics[:3]:
        lines.append(f"- {t['topic']}: Master {t['target_level']} concepts")
    lines.append("\n**Month 2: Applied Practice**")
    for t in topics[2:5]:
        lines.append(f"- {t['topic']}: Build projects and solve problems")
    lines.append("\n**Month 3: Mastery & Interview Prep**")
    lines.append("- Mock interviews covering all weak areas\n- Practice explaining concepts out loud")
    return "\n".join(lines)


def _generate_advice(name: str, score: float, topic_plans: List[Dict], strong: List[str]) -> str:
    parts = []
    if score >= 70:
        parts.append(f"Great job, {name}! You scored {score:.0f}/100. Your strengths in {', '.join(strong[:3]) if strong else 'several areas'} are impressive.")
    elif score >= 50:
        parts.append(f"{name}, you scored {score:.0f}/100 — a decent starting point with clear room for improvement.")
    else:
        parts.append(f"{name}, your score of {score:.0f}/100 indicates areas to focus on, but don't be discouraged.")

    if topic_plans:
        worst = topic_plans[0]
        parts.append(f"Start with {worst['topic']} — structured learning can move you from {worst['current_level']} to {worst['target_level']} in about {worst['estimated_time']}.")

    parts.append("Consistency is key — even 30 minutes of focused practice daily adds up quickly. You've got this!")
    return "\n\n".join(parts)
