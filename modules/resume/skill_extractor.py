"""Skill extraction using spaCy NER, custom skill taxonomy, and optional HF NER enrichment."""

import logging
import re
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger(__name__)

_nlp = None


def _get_nlp():
    global _nlp
    if _nlp is None:
        try:
            import spacy
            from app.config import SPACY_MODEL
            try:
                _nlp = spacy.load(SPACY_MODEL)
            except OSError:
                logger.warning("spaCy model %s not found, downloading...", SPACY_MODEL)
                from spacy.cli import download
                download(SPACY_MODEL)
                _nlp = spacy.load(SPACY_MODEL)
        except ImportError:
            logger.warning("spaCy not available, using regex-only extraction")
            _nlp = False
    return _nlp if _nlp else None


def extract_skills(text: str, use_ner: bool = False) -> List[str]:
    """Extract skills from resume text.

    Args:
        text:    Resume text (or skills section text).
        use_ner: When True, also calls the HuggingFace ``yashpwr/resume-ner-bert``
                 model to surface skills that the taxonomy may miss.
                 Requires ``transformers`` and ``torch``.

    Returns:
        Sorted list of unique extracted skills.
    """
    from app.constants import ALL_SKILLS

    skills_found: Set[str] = set()
    text_lower = text.lower()

    # Method 1: Taxonomy matching
    for skill in ALL_SKILLS:
        pattern = r'\b' + re.escape(skill.lower()) + r'\b'
        if re.search(pattern, text_lower):
            skills_found.add(skill.lower())

    # Method 2: spaCy NER
    nlp = _get_nlp()
    if nlp:
        try:
            doc = nlp(text)
            for ent in doc.ents:
                if ent.label_ in ("ORG", "PRODUCT", "WORK_OF_ART"):
                    ent_lower = ent.text.lower().strip()
                    for skill in ALL_SKILLS:
                        if skill.lower() in ent_lower or ent_lower in skill.lower():
                            skills_found.add(skill.lower())
        except Exception as e:
            logger.warning("spaCy NER failed: %s", e)

    # Method 3: Regex patterns for common formats
    skill_patterns = [
        r'\b[A-Z][a-z]+(?:\.[a-z]+)+\b',
        r'\b[A-Z]\+\+\b',
        r'\b[A-Z]#\b',
        r'\b(?:AWS|GCP|CI/CD|REST|API|SQL|NoSQL|HTML|CSS|JSON|XML|YAML|SSH|TCP|UDP)\b',
    ]
    for pattern in skill_patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            skills_found.add(match.lower())

    # Method 4: HuggingFace NER enrichment (opt-in)
    if use_ner:
        try:
            from modules.resume.ner_parser import _get_ner_pipeline
            pipeline = _get_ner_pipeline()
            ner_results = pipeline(text[:12000])
            for item in ner_results:
                label = str(item.get("entity_group", "")).upper()
                value = str(item.get("word", "")).strip()
                if label in {"SKILL", "TECHNOLOGY"} and value and len(value) > 1:
                    skills_found.add(value.lower())
        except Exception as exc:
            logger.warning("HuggingFace NER enrichment skipped: %s", exc)

    categorized = categorize_skills(list(skills_found))
    logger.info(
        "Extracted %d skills across %d categories (ner=%s)",
        len(skills_found), len(categorized), use_ner,
    )
    return sorted(skills_found)


def categorize_skills(skills: List[str]) -> Dict[str, List[str]]:
    from app.constants import SKILL_TAXONOMY
    categorized: Dict[str, List[str]] = {cat: [] for cat in SKILL_TAXONOMY}
    categorized["other"] = []
    for skill in skills:
        skill_lower = skill.lower()
        found = False
        for category, category_skills in SKILL_TAXONOMY.items():
            if skill_lower in [s.lower() for s in category_skills]:
                categorized[category].append(skill)
                found = True
                break
        if not found:
            categorized["other"].append(skill)
    return {k: v for k, v in categorized.items() if v}


def extract_projects(text: str) -> List[str]:
    projects: List[str] = []
    lines = text.split("\n")
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        cleaned = re.sub(r'^[\-•*▪►▸▹●○◆◇■□★☆→➜❯]+\s*', '', stripped).strip()
        if 3 < len(cleaned) < 200:
            if re.match(r'^(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|20\d{2})', cleaned, re.IGNORECASE):
                continue
            if re.match(r'^(?:Technologies|Tech Stack|Tools|Skills used):', cleaned, re.IGNORECASE):
                continue
            projects.append(cleaned)
    return projects[:20]


def extract_candidate_info(text: str) -> Dict[str, Any]:
    info: Dict[str, Any] = {}
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    emails = re.findall(email_pattern, text)
    if emails:
        info["email"] = emails[0]
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    if lines:
        first_line = lines[0]
        if (not re.search(email_pattern, first_line)
                and not re.search(r'\d{3}[-.\s]?\d{3}[-.\s]?\d{4}', first_line)
                and not first_line.startswith("http")
                and len(first_line) < 60):
            info["name"] = first_line
    phone_pattern = r'[\+]?[(]?[0-9]{1,4}[)]?[-\s\./0-9]{7,15}'
    phones = re.findall(phone_pattern, text)
    if phones:
        info["phone"] = phones[0]
    return info


def build_full_profile(
    pdf_path: str,
    use_ner: bool = True,
) -> Dict[str, Any]:
    """Convenience function: parse a resume PDF and return a complete enriched profile.

    Combines section segmentation, contact extraction, skill extraction,
    and optional HuggingFace NER entity detection into one call.

    Args:
        pdf_path: Path to the resume PDF.
        use_ner:  When True, uses ``yashpwr/resume-ner-bert`` for entity enrichment.

    Returns:
        A unified profile dict ready to pass into ``RAGChain.load_ner_profile()``.
    """
    if use_ner:
        from modules.resume.ner_parser import parse_resume_with_ner
        profile = parse_resume_with_ner(pdf_path)
        # Merge skill extractor results on top of NER skills
        extra_skills = extract_skills(profile["raw_text"], use_ner=False)
        combined = sorted(set(profile.get("skills", []) + extra_skills))
        profile["skills"] = combined
        return profile
    else:
        from modules.resume.parser import extract_sections
        from modules.resume.skill_extractor import extract_candidate_info
        sections = extract_sections(pdf_path)
        raw_text = "\n\n".join(sections.values())
        skills = extract_skills(raw_text, use_ner=False)
        info = extract_candidate_info(raw_text)
        return {
            "raw_text": raw_text,
            "sections": sections,
            "skills": skills,
            "organizations": [],
            "education": [],
            "designation": [],
            "entities": [],
            **info,
        }
