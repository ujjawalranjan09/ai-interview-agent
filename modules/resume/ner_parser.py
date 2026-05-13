"""Resume NER parser using Hugging Face dslim/bert-base-NER.

Extracts structured candidate entities (name, organisations, locations)
and combines with rule-based technical-skill detection tailored for
Software / ML / Data-Science resumes.

Reference model: https://huggingface.co/dslim/bert-base-NER
"""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

_NER_PIPELINE = None
_MODEL_NAME = "dslim/bert-base-NER"

KNOWN_SKILLS: set[str] = {
    "python", "java", "c++", "javascript", "typescript", "sql",
    "mongodb", "mysql", "postgresql", "redis",
    "fastapi", "flask", "django", "streamlit",
    "docker", "kubernetes", "git", "github", "linux",
    "rest", "api", "graphql",
    "machine learning", "deep learning", "tensorflow", "pytorch",
    "opencv", "nlp", "rag", "chromadb", "faiss",
    "transformers", "spacy", "whisper", "sentence-transformers",
    "plotly", "pandas", "numpy", "scikit-learn",
    "react", "node.js", "html", "css",
}


def _get_ner_pipeline():
    global _NER_PIPELINE
    if _NER_PIPELINE is None:
        from transformers import pipeline  # noqa: PLC0415
        logger.info("Loading HuggingFace NER model: %s", _MODEL_NAME)
        _NER_PIPELINE = pipeline(
            "ner",
            model=_MODEL_NAME,
            tokenizer=_MODEL_NAME,
            aggregation_strategy="simple",
        )
    return _NER_PIPELINE


def extract_resume_text_from_pdf(pdf_path: str) -> str:
    """Extract plain text from a PDF resume file."""
    import pdfplumber  # noqa: PLC0415
    pages: list[str] = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            pages.append(page.extract_text() or "")
    return "\n".join(pages).strip()


def parse_resume_text(text: str) -> Dict[str, Any]:
    """Return a structured candidate profile dict from raw resume text."""
    ner = _get_ner_pipeline()

    # bert-base-NER has 512 token limit; take first 8 000 chars as proxy
    entities: list[dict] = ner(text[:8_000])

    people: list[str] = []
    organisations: list[str] = []
    locations: list[str] = []
    misc: list[str] = []
    for ent in entities:
        word = ent.get("word", "").strip()
        if not word:
            continue
        group = ent.get("entity_group", "")
        if group == "PER":
            people.append(word)
        elif group == "ORG":
            organisations.append(word)
        elif group == "LOC":
            locations.append(word)
        elif group == "MISC":
            misc.append(word)

    skills = extract_skills(text)
    emails = re.findall(
        r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}", text
    )
    phones = re.findall(r"(?:\+91[\-\s]?)?[6-9]\d{9}", text)

    return {
        "name": people[0] if people else "",
        "emails": sorted(set(emails)),
        "phones": sorted(set(phones)),
        "organisations": _dedupe(organisations),
        "locations": _dedupe(locations),
        "skills": skills,
        "top_keywords": _top_keywords(text),
        "raw_entities": {
            "people": _dedupe(people),
            "misc": _dedupe(misc),
        },
        "candidate_summary": _build_summary(text, skills, organisations),
    }


def extract_skills(text: str) -> List[str]:
    """Rule-based skill extractor using a curated tech-skill vocabulary."""
    lower = text.lower()
    return sorted(skill for skill in KNOWN_SKILLS if skill in lower)


def _build_summary(
    text: str, skills: List[str], organisations: List[str]
) -> str:
    parts: list[str] = []
    if skills:
        parts.append("Skills: " + ", ".join(skills[:12]))
    if organisations:
        parts.append("Organisations: " + ", ".join(organisations[:5]))
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    if lines:
        excerpt = " ".join(lines[:3])[:400]
        parts.append("Excerpt: " + excerpt)
    return " | ".join(parts)


def _top_keywords(text: str, limit: int = 20) -> List[str]:
    STOP = {
        "the", "and", "for", "with", "that", "this", "from", "have",
        "using", "your", "you", "are", "was", "not", "but", "will",
        "can", "into", "use", "used", "also", "have",
    }
    words = re.findall(r"[A-Za-z][A-Za-z+.#\-]{2,}", text.lower())
    freq: dict[str, int] = {}
    for w in words:
        if w in STOP:
            continue
        freq[w] = freq.get(w, 0) + 1
    ranked = sorted(freq.items(), key=lambda kv: (-kv[1], kv[0]))
    return [w for w, _ in ranked[:limit]]


def _dedupe(items: List[str]) -> List[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        key = item.lower()
        if key not in seen:
            seen.add(key)
            out.append(item)
    return out
