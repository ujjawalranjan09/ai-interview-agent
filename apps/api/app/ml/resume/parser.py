"""PDF resume parser with section segmentation."""

import io
import logging
import re
from typing import Dict, List

logger = logging.getLogger(__name__)

SECTION_PATTERNS = [
    r"(?i)^(?:professional\s+)?(?:summary|profile|objective|about\s+me)\s*$",
    r"(?i)^(?:work\s+)?experience\s*$",
    r"(?i)^(?:employment\s+)?history\s*$",
    r"(?i)^education\s*$",
    r"(?i)^(?:technical\s+)?skills?\s*$",
    r"(?i)^(?:technical\s+)?(?:competencies|expertise)\s*$",
    r"(?i)^projects?\s*$",
    r"(?i)^(?:key\s+)?projects?\s*$",
    r"(?i)^(?:certifications?|licenses?)\s*$",
    r"(?i)^(?:awards?|achievements?|honors?)\s*$",
    r"(?i)^(?:publications?)\s*$",
    r"(?i)^(?:volunteer|community)\s*(?:experience|work)?\s*$",
    r"(?i)^languages?\s*$",
    r"(?i)^(?:references?)\s*$",
    r"(?i)^(?:additional\s+)?(?:information|info)\s*$",
    r"(?i)^(?:internships?)\s*$",
]

SECTION_NAME_MAP = {
    "summary": "summary", "professional summary": "summary", "profile": "summary",
    "objective": "summary", "about me": "summary",
    "experience": "experience", "work experience": "experience",
    "employment history": "experience", "history": "experience",
    "education": "education",
    "skills": "skills", "skill": "skills", "technical skills": "skills",
    "competencies": "skills", "expertise": "skills",
    "projects": "projects", "project": "projects", "key projects": "projects",
    "certifications": "certifications", "licenses": "certifications",
    "awards": "awards", "achievements": "awards", "honors": "awards",
    "publications": "publications",
    "volunteer experience": "volunteer", "volunteer work": "volunteer",
    "volunteer": "volunteer",
    "languages": "languages",
    "references": "references",
    "additional information": "additional_info", "additional info": "additional_info",
    "internships": "internships",
}


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    try:
        import pdfplumber
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            parts = [page.extract_text() or "" for page in pdf.pages]
        text = "\n".join(parts).strip()
        if text:
            return text
    except Exception as e:
        logger.warning("pdfplumber failed: %s", e)

    try:
        from PyPDF2 import PdfReader
        reader = PdfReader(io.BytesIO(pdf_bytes))
        parts = [page.extract_text() or "" for page in reader.pages]
        return "\n".join(parts)
    except Exception as e:
        logger.error("PyPDF2 also failed: %s", e)
        raise RuntimeError(f"Could not extract text from PDF: {e}")


def _normalize_section_name(raw: str) -> str:
    name = raw.strip().lower()
    return SECTION_NAME_MAP.get(name, name.replace(" ", "_"))


def segment_resume(text: str) -> Dict[str, str]:
    lines = text.split("\n")
    sections: Dict[str, str] = {}
    current_section = "header"
    current_content: List[str] = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            current_content.append("")
            continue

        matched = False
        for pattern in SECTION_PATTERNS:
            if re.match(pattern, stripped):
                if current_content:
                    sections[current_section] = "\n".join(current_content).strip()
                current_section = _normalize_section_name(stripped)
                current_content = []
                matched = True
                break

        if not matched:
            current_content.append(line)

    if current_content:
        sections[current_section] = "\n".join(current_content).strip()

    return sections


def extract_sections(pdf_bytes: bytes) -> Dict[str, str]:
    raw_text = extract_text_from_pdf(pdf_bytes)
    sections = segment_resume(raw_text)
    logger.info("Extracted %d sections from resume", len(sections))
    return sections
