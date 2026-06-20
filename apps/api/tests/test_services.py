"""Service-level unit tests."""

from app.services.copilot_service import select_suggestion_types, render_suggestion
from app.services.jd_service import extract_skills_from_jd, calculate_match, generate_jd_questions


def test_copilot_select_suggestion_types_low_score():
    types = select_suggestion_types(30)
    assert "rephrase" in types
    assert "encourage" in types
    assert "gap_fill" in types


def test_copilot_select_suggestion_types_mid_score():
    types = select_suggestion_types(65)
    assert "follow_up" in types
    assert "star_method" in types
    assert "gap_fill" in types


def test_copilot_select_suggestion_types_high_score():
    types = select_suggestion_types(90)
    assert "probe_deeper" in types
    assert "strong_area" in types
    assert "gap_fill" in types


def test_copilot_render_suggestion():
    result = render_suggestion("follow_up", {"topic": "Python", "skill": "testing", "concept": "debugging"})
    assert "id" in result
    assert "type" in result
    assert "text" in result
    assert result["type"] == "follow_up"


def test_jd_extract_skills():
    text = "Required:\npython\njavascript\n\nPreferred:\naws\ndocker\n"
    result = extract_skills_from_jd(text)
    assert "python" in result["required_skills"]
    assert "javascript" in result["required_skills"]
    assert "aws" in result["preferred_skills"]
    assert "docker" in result["preferred_skills"]


def test_jd_calculate_match():
    candidate_skills = ["python", "javascript", "react"]
    jd_skills = {"required_skills": ["python", "go"], "preferred_skills": ["react", "aws"]}
    result = calculate_match(candidate_skills, jd_skills)
    assert result["match_percentage"] == 50.0
    assert "python" in result["matched_required"]
    assert "go" in result["missing_required"]
    assert "react" in result["matched_preferred"]


def test_jd_generate_questions():
    questions = generate_jd_questions(["python", "docker"], 2)
    assert len(questions) <= 2
    for q in questions:
        assert "question_text" in q
        assert "target_skill" in q
