import re
import random

from app.core.constants import ALL_SKILLS, TECHNICAL_QUESTION_TEMPLATES


def extract_skills_from_jd(jd_text: str) -> dict:
    text = jd_text.lower()
    lines = text.split('\n')
    required_skills = []
    preferred_skills = []

    # Build a map of line index → section type based on headers
    line_section: dict[int, str] = {}
    current_section = "required"  # default
    for i, line in enumerate(lines):
        stripped = line.strip()
        if any(w in stripped for w in ["preferred", "nice to have", "bonus"]):
            current_section = "preferred"
        elif any(w in stripped for w in ["required", "must have", "essential"]):
            current_section = "required"
        line_section[i] = current_section

    # Find which line each skill appears on
    for skill in ALL_SKILLS:
        pattern = r'\b' + re.escape(skill) + r'\b'
        match = re.search(pattern, text)
        if not match:
            continue

        # Find the line number for this match
        char_pos = match.start()
        line_num = text[:char_pos].count('\n')
        section = line_section.get(line_num, "required")

        if section == "preferred":
            preferred_skills.append(skill)
        else:
            required_skills.append(skill)

    return {"required_skills": required_skills, "preferred_skills": preferred_skills}


def calculate_match(candidate_skills: list[str], jd_skills: dict) -> dict:
    candidate_lower = [s.lower() for s in candidate_skills]
    matched_required = [s for s in jd_skills["required_skills"] if s in candidate_lower]
    missing_required = [s for s in jd_skills["required_skills"] if s not in candidate_lower]
    matched_preferred = [s for s in jd_skills["preferred_skills"] if s in candidate_lower]
    missing_preferred = [s for s in jd_skills["preferred_skills"] if s not in candidate_lower]

    total_required = len(jd_skills["required_skills"])
    match_percentage = round(
        (len(matched_required) / total_required * 100) if total_required > 0 else 100.0, 1
    )

    return {
        "match_percentage": match_percentage,
        "matched_required": matched_required,
        "missing_required": missing_required,
        "matched_preferred": matched_preferred,
        "missing_preferred": missing_preferred,
    }


def generate_jd_questions(missing_skills: list[str], count: int = 5) -> list[dict]:
    templates = TECHNICAL_QUESTION_TEMPLATES.get("medium", [])
    questions = []
    for skill in missing_skills[:count]:
        template = random.choice(templates)
        rendered = template.replace("{skill}", skill).replace("{other_skill}", "related technology")
        questions.append({
            "question_text": rendered,
            "question_type": "technical",
            "difficulty": "medium",
            "target_skill": skill,
        })
    return questions
