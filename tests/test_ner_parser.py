"""Unit tests for modules/resume/ner_parser.py.

All tests mock the HuggingFace pipeline so no model download is needed
during CI.
"""

from unittest.mock import MagicMock, patch

import pytest

from modules.resume.ner_parser import (
    _dedupe,
    _top_keywords,
    extract_skills,
    parse_resume_text,
)

SAMPLE_RESUME = """
Ujjawal Ranjan
Email: ujjawal@example.com | Phone: 9876543210
Skills: Python, FastAPI, MongoDB, Docker, TensorFlow, React
Experience: Infosys | Jaipur
Project: AI Interview Agent using Python and Streamlit
"""


@pytest.fixture()
def mock_ner():
    """Patch _get_ner_pipeline to return deterministic entities."""
    entities = [
        {"entity_group": "PER", "word": "Ujjawal Ranjan", "score": 0.99},
        {"entity_group": "ORG", "word": "Infosys", "score": 0.97},
        {"entity_group": "LOC", "word": "Jaipur", "score": 0.96},
    ]
    mock_pipe = MagicMock(return_value=entities)
    with patch("modules.resume.ner_parser._get_ner_pipeline", return_value=mock_pipe):
        yield mock_pipe


def test_extract_skills():
    skills = extract_skills(SAMPLE_RESUME)
    assert "python" in skills
    assert "fastapi" in skills
    assert "mongodb" in skills
    assert "docker" in skills


def test_parse_resume_returns_name(mock_ner):
    result = parse_resume_text(SAMPLE_RESUME)
    assert result["name"] == "Ujjawal Ranjan"


def test_parse_resume_returns_org(mock_ner):
    result = parse_resume_text(SAMPLE_RESUME)
    assert "Infosys" in result["organisations"]


def test_parse_resume_returns_location(mock_ner):
    result = parse_resume_text(SAMPLE_RESUME)
    assert "Jaipur" in result["locations"]


def test_parse_resume_emails(mock_ner):
    result = parse_resume_text(SAMPLE_RESUME)
    assert "ujjawal@example.com" in result["emails"]


def test_parse_resume_phones(mock_ner):
    result = parse_resume_text(SAMPLE_RESUME)
    assert "9876543210" in result["phones"]


def test_dedupe_preserves_order():
    assert _dedupe(["Infosys", "TCS", "infosys"]) == ["Infosys", "TCS"]


def test_top_keywords_returns_list():
    kw = _top_keywords(SAMPLE_RESUME)
    assert isinstance(kw, list)
    assert len(kw) <= 20
