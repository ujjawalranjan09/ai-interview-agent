"""Tests for Hugging Face NER resume parser helpers."""

from modules.resume.ner_parser import _extract_contacts


def test_extract_contacts_from_resume_text():
    text = """
    Ujjawal Ranjan
    ujjawal@example.com
    +91 9876543210
    https://github.com/ujjawalranjan09
    https://linkedin.com/in/ujjawalranjan
    """
    result = _extract_contacts(text)
    assert "ujjawal@example.com" in result["emails"]
    assert any("9876543210" in p for p in result["phones"])
    assert any("github.com/ujjawalranjan09" in l for l in result["links"])
