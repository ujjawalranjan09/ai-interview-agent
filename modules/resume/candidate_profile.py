"""Candidate profile builder — combines NER, skill extraction, and summary.

Downstream modules (RAG, adaptive questioning, evaluation) should call
``build_candidate_profile`` to get a standardised profile dict.
"""

from __future__ import annotations

from typing import Any, Dict

from modules.resume.ner_parser import (
    extract_resume_text_from_pdf,
    parse_resume_text,
)


def build_candidate_profile(
    resume_path: str = "",
    resume_text: str = "",
) -> Dict[str, Any]:
    """Return a structured candidate profile dict.

    Parameters
    ----------
    resume_path:
        Path to a PDF resume file (used when resume_text is empty).
    resume_text:
        Raw resume text (takes priority over resume_path).

    Returns
    -------
    dict with keys: ``candidate`` (parsed entities + skills),
    ``resume_text`` (raw string), ``profile_version``.
    """
    if not resume_text and resume_path:
        resume_text = extract_resume_text_from_pdf(resume_path)

    parsed = parse_resume_text(resume_text)

    return {
        "candidate": parsed,
        "resume_text": resume_text,
        "profile_version": "2.0",
    }
