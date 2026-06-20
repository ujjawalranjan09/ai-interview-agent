"""Skill extraction using spaCy NER and custom skill taxonomy."""

import logging
import re
from typing import Dict, List, Set

logger = logging.getLogger(__name__)

_nlp = None


def _get_nlp():
    global _nlp
    if _nlp is None:
        try:
            import spacy
            from app.core.config import settings
            try:
                _nlp = spacy.load(settings.SPACY_MODEL)
            except OSError:
                from spacy.cli import download
                download(settings.SPACY_MODEL)
                _nlp = spacy.load(settings.SPACY_MODEL)
        except ImportError:
            logger.warning("spaCy not available, using regex-only extraction")
            _nlp = False
    return _nlp if _nlp else None


def extract_skills(text: str) -> List[str]:
    from app.core.constants import ALL_SKILLS
    skills_found: Set[str] = set()
    text_lower = text.lower()

    for skill in ALL_SKILLS:
        pattern = r'\b' + re.escape(skill.lower()) + r'\b'
        if re.search(pattern, text_lower):
            skills_found.add(skill.lower())

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

    skill_patterns = [
        r'\b[A-Z][a-z]+(?:\.[a-z]+)+\b',
        r'\b[A-Z]\+\+\b',
        r'\b[A-Z]#\b',
        r'\b(?:AWS|GCP|CI/CD|REST|API|SQL|NoSQL|HTML|CSS|JSON|XML|YAML|SSH|TCP|UDP)\b',
    ]
    for pattern in skill_patterns:
        for match in re.findall(pattern, text):
            skills_found.add(match.lower())

    return sorted(skills_found)


def categorize_skills(skills: List[str]) -> Dict[str, List[str]]:
    from app.core.constants import SKILL_TAXONOMY
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
    for line in text.split("\n"):
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


def extract_candidate_info(text: str) -> Dict[str, str]:
    info: Dict[str, str] = {}
    emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
    if emails:
        info["email"] = emails[0]

    lines = [line.strip() for line in text.split("\n") if line.strip()]
    if lines:
        first_line = lines[0]
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        if not re.search(email_pattern, first_line) and not re.search(r'\d{3}[-.\s]?\d{3}[-.\s]?\d{4}', first_line):
            if not first_line.startswith("http") and len(first_line) < 60:
                info["name"] = first_line

    phones = re.findall(r'[\+]?[(]?[0-9]{1,4}[)]?[-\s\./0-9]{7,15}', text)
    if phones:
        info["phone"] = phones[0]

    return info
