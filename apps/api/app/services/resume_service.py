"""Resume processing service — orchestrate parse + extract."""

import logging
from typing import Any, Dict

from app.ml.resume.parser import extract_sections
from app.ml.resume.skill_extractor import extract_skills, extract_projects, extract_candidate_info

logger = logging.getLogger(__name__)


def process_resume(pdf_bytes: bytes) -> Dict[str, Any]:
    sections = extract_sections(pdf_bytes)
    full_text = "\n".join(sections.values())

    skills = extract_skills(full_text)
    projects = extract_projects(sections.get("projects", full_text))
    candidate_info = extract_candidate_info(full_text)

    logger.info("Resume processed: %d skills, %d projects", len(skills), len(projects))

    return {
        "skills": skills,
        "projects": projects,
        "candidate_info": candidate_info,
        "sections": sections,
    }
