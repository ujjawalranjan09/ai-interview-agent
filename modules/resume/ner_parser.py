"""Hugging Face NER-powered resume parser.

Adds structured entity extraction on top of the existing PDF parsing and section
segmentation pipeline.
"""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, List

from .parser import extract_text_from_pdf, segment_resume

logger = logging.getLogger(__name__)

_ner_pipeline = None


def _get_ner_pipeline():
    global _ner_pipeline
    if _ner_pipeline is None:
        try:
            from transformers import pipeline
        except ImportError as exc:
            raise ImportError(
                "transformers is required for NER resume parsing. Install with: pip install transformers torch"
            ) from exc

        model_name = "yashpwr/resume-ner-bert"
        _ner_pipeline = pipeline(
            "ner",
            model=model_name,
            tokenizer=model_name,
            aggregation_strategy="simple",
        )
        logger.info("Loaded Hugging Face resume NER model: %s", model_name)
    return _ner_pipeline


def _extract_contacts(text: str) -> Dict[str, List[str]]:
    emails = re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)
    phones = re.findall(r"[\+]?[(]?[0-9]{1,4}[)]?[-\s\./0-9]{7,15}", text)
    links = re.findall(r"https?://\S+|www\.\S+|linkedin\.com/\S+|github\.com/\S+", text, re.IGNORECASE)
    return {
        "emails": sorted(set(e.strip() for e in emails)),
        "phones": sorted(set(p.strip() for p in phones if len(re.sub(r"\D", "", p)) >= 10)),
        "links": sorted(set(l.strip() for l in links)),
    }


def parse_resume_with_ner(pdf_path: str) -> Dict[str, Any]:
    """Parse a resume PDF into structured sections and entities."""
    raw_text = extract_text_from_pdf(pdf_path)
    sections = segment_resume(raw_text)
    ner = _get_ner_pipeline()
    entities = ner(raw_text[:12000])

    structured: Dict[str, Any] = {
        "raw_text": raw_text,
        "sections": sections,
        "entities": entities,
        "skills": [],
        "organizations": [],
        "education": [],
        "designation": [],
        "name": None,
    }

    contacts = _extract_contacts(raw_text)
    structured.update(contacts)

    for item in entities:
        label = str(item.get("entity_group", "")).upper()
        value = str(item.get("word", "")).strip()
        if not value:
            continue

        if label in {"NAME", "PER"} and not structured["name"]:
            structured["name"] = value
        elif label in {"SKILL", "TECHNOLOGY"}:
            structured["skills"].append(value)
        elif label in {"ORG", "ORGANIZATION", "COMPANY"}:
            structured["organizations"].append(value)
        elif label in {"DEGREE", "EDUCATION", "COLLEGE", "UNIVERSITY"}:
            structured["education"].append(value)
        elif label in {"DESIGNATION", "ROLE", "TITLE"}:
            structured["designation"].append(value)

    for key in ["skills", "organizations", "education", "designation"]:
        structured[key] = sorted({v.strip() for v in structured[key] if v and len(v.strip()) > 1})

    return structured
