"""RAG chain — generates targeted interview questions from resume + job description."""

import json
import logging
import os
from typing import Any, Dict, List, Optional

from modules.rag.retriever import Retriever

logger = logging.getLogger(__name__)


class RAGChain:
    """Retrieval-Augmented Generation chain for interview question creation.

    Takes a candidate resume and a job description, retrieves relevant
    requirements, and generates targeted questions that match candidate
    skills to job requirements.

    Args:
        retriever:    An initialized Retriever with indexed job description.
        model:        OpenAI model name (default from config).
        ner_profile:  Optional structured NER result from ``parse_resume_with_ner()``.
                      When provided, the chain enriches the prompt with
                      organisations, designations, and education context so that
                      generated questions are more targeted.
    """

    def __init__(
        self,
        retriever: Retriever,
        model: Optional[str] = None,
        ner_profile: Optional[Dict[str, Any]] = None,
    ):
        self.retriever = retriever
        self.ner_profile = ner_profile or {}
        if model is None:
            try:
                from app.config import OPENAI_MODEL
                self.model = OPENAI_MODEL
            except ImportError:
                self.model = "gpt-3.5-turbo"
        self._openai_key = os.getenv("OPENAI_API_KEY", "")

    @property
    def has_llm(self) -> bool:
        return bool(self._openai_key)

    # ── Public helpers for NER enrichment ────────────────────────────────────

    def load_ner_profile(self, ner_profile: Dict[str, Any]) -> None:
        """Attach a NER profile produced by ``parse_resume_with_ner()``.

        Can be called after construction — e.g. once the PDF upload completes.
        """
        self.ner_profile = ner_profile

    def _ner_context(self) -> str:
        """Build a compact NER context string to inject into prompts."""
        if not self.ner_profile:
            return ""
        parts = []
        if self.ner_profile.get("name"):
            parts.append(f"Candidate name: {self.ner_profile['name']}")
        if self.ner_profile.get("organizations"):
            parts.append(f"Companies/Orgs on resume: {', '.join(self.ner_profile['organizations'][:5])}")
        if self.ner_profile.get("education"):
            parts.append(f"Education entities: {', '.join(self.ner_profile['education'][:3])}")
        if self.ner_profile.get("designation"):
            parts.append(f"Roles/Designations: {', '.join(self.ner_profile['designation'][:3])}")
        return "\n".join(parts)

    # ── Core methods (unchanged public API) ───────────────────────────────────

    def generate_questions(
        self,
        candidate_skills: List[str],
        candidate_projects: List[str],
        candidate_experience: str = "",
        num_questions: int = 5,
        difficulty: str = "medium",
    ) -> List[Dict[str, Any]]:
        requirements = self.retriever.retrieve_requirements(
            candidate_skills, top_k=max(5, num_questions)
        )
        req_text = "\n".join(
            f"- {chunk.text} (relevance: {score:.2f}, skill: {skill})"
            for chunk, score, skill in requirements
        )
        if not req_text:
            req_text = "(No specific requirements matched from job description)"

        if self.has_llm:
            return self._generate_with_llm(
                candidate_skills=candidate_skills,
                candidate_projects=candidate_projects,
                candidate_experience=candidate_experience,
                requirements_text=req_text,
                num_questions=num_questions,
                difficulty=difficulty,
            )
        return self._generate_from_templates(
            candidate_skills=candidate_skills,
            candidate_projects=candidate_projects,
            requirements=requirements,
            num_questions=num_questions,
            difficulty=difficulty,
        )

    def identify_gaps(
        self,
        candidate_skills: List[str],
    ) -> List[Dict[str, Any]]:
        all_text = self.retriever.get_all_text()
        gaps: List[Dict[str, Any]] = []
        import re
        req_sentences = re.split(r"[.\n]", all_text)
        candidate_skills_lower = {s.lower() for s in candidate_skills}
        requirement_keywords = ["required", "must have", "essential", "necessary", "minimum"]
        nice_to_have_keywords = ["preferred", "nice to have", "bonus", "plus", "desirable"]
        for sentence in req_sentences:
            sentence_lower = sentence.lower().strip()
            if not sentence_lower or len(sentence_lower) < 10:
                continue
            is_required = any(kw in sentence_lower for kw in requirement_keywords)
            is_nice = any(kw in sentence_lower for kw in nice_to_have_keywords)
            if not (is_required or is_nice):
                continue
            try:
                from app.constants import ALL_SKILLS
            except ImportError:
                ALL_SKILLS = []
            mentioned_skills = [s for s in ALL_SKILLS if s in sentence_lower]
            for skill in mentioned_skills:
                if skill not in candidate_skills_lower:
                    severity = "high" if is_required else "medium"
                    gaps.append({
                        "required_skill": skill,
                        "description": sentence.strip(),
                        "severity": severity,
                        "suggestion": f"Your resume doesn't mention {skill}, which is {'required' if is_required else 'preferred'} for this role.",
                    })
        seen = set()
        unique_gaps = []
        for gap in gaps:
            if gap["required_skill"] not in seen:
                seen.add(gap["required_skill"])
                unique_gaps.append(gap)
        return unique_gaps

    def generate_gap_questions(
        self,
        gaps: List[Dict[str, Any]],
        max_questions: int = 3,
    ) -> List[Dict[str, Any]]:
        questions: List[Dict[str, Any]] = []
        for gap in gaps[:max_questions]:
            skill = gap["required_skill"]
            severity = gap["severity"]
            if severity == "high":
                question_text = (
                    f"This role requires experience with {skill}. "
                    f"Can you tell me about any experience you have with {skill}, "
                    f"even if it's from personal projects or self-study?"
                )
            else:
                question_text = (
                    f"The job description mentions {skill} as a preferred skill. "
                    f"How familiar are you with {skill}?"
                )
            questions.append({
                "question": question_text,
                "type": "gap_probe",
                "target_skill": skill,
                "job_requirement": gap.get("description", ""),
                "rationale": gap.get("suggestion", ""),
                "severity": severity,
            })
        return questions

    # ── LLM generation ────────────────────────────────────────────────────────

    def _generate_with_llm(
        self,
        candidate_skills: List[str],
        candidate_projects: List[str],
        candidate_experience: str,
        requirements_text: str,
        num_questions: int,
        difficulty: str,
    ) -> List[Dict[str, Any]]:
        ner_ctx = self._ner_context()
        prompt = (
            "You are an expert technical interviewer. Generate interview questions that match "
            "the candidate's background to the job requirements.\n\n"
            f"Candidate Skills: {', '.join(candidate_skills)}\n"
            f"Candidate Projects: {', '.join(candidate_projects)}\n"
            f"Experience: {candidate_experience}\n"
            + (f"\nAdditional Resume Context (from NER):\n{ner_ctx}\n" if ner_ctx else "")
            + f"\nRelevant Job Requirements:\n{requirements_text}\n\n"
            f"Difficulty: {difficulty}\n"
            f"Number of questions: {num_questions}\n\n"
            "For each question, provide:\n"
            "1. The question text\n"
            "2. Question type (technical/behavioral/resume/gap_probe)\n"
            "3. The target skill being tested\n"
            "4. The job requirement it relates to\n"
            "5. Why this question is relevant (rationale)\n\n"
            "Return valid JSON array: "
            '[{"question": "...", "type": "...", "target_skill": "...", '
            '"job_requirement": "...", "rationale": "..."}]'
        )
        try:
            import openai
            client = openai.OpenAI(api_key=self._openai_key)
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a precise interview question generator. Always return valid JSON."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
                max_tokens=2000,
            )
            content = response.choices[0].message.content.strip()
            questions = self._parse_json_response(content)
            return questions[:num_questions]
        except Exception as exc:
            logger.error("LLM generation failed: %s, falling back to templates", exc)
            return self._generate_from_templates(
                candidate_skills, candidate_projects, [], num_questions, difficulty,
            )

    def _generate_from_templates(
        self,
        candidate_skills: List[str],
        candidate_projects: List[str],
        requirements: list,
        num_questions: int,
        difficulty: str,
    ) -> List[Dict[str, Any]]:
        try:
            from app.constants import TECHNICAL_QUESTION_TEMPLATES, RESUME_QUESTION_TEMPLATES
        except ImportError:
            TECHNICAL_QUESTION_TEMPLATES = {
                "easy": ["Can you explain {skill}?"],
                "medium": ["How would you use {skill} in a project?"],
                "hard": ["How would you architect a system using {skill}?"],
                "expert": ["What are the trade-offs of {skill}?"],
            }
            RESUME_QUESTION_TEMPLATES = [
                "Tell me about your project '{project}'.",
                "How did you use {skill} in your work?",
            ]
        templates = TECHNICAL_QUESTION_TEMPLATES.get(difficulty, TECHNICAL_QUESTION_TEMPLATES["medium"])
        questions: List[Dict[str, Any]] = []
        skill_idx = 0
        template_idx = 0
        while len(questions) < num_questions and candidate_skills:
            skill = candidate_skills[skill_idx % len(candidate_skills)]
            template = templates[template_idx % len(templates)]
            question_text = template.format(
                skill=skill,
                other_skill=candidate_skills[(skill_idx + 1) % len(candidate_skills)]
                if len(candidate_skills) > 1
                else "a related technology",
            )
            questions.append({
                "question": question_text,
                "type": "technical",
                "target_skill": skill,
                "job_requirement": "",
                "rationale": f"Testing {skill} knowledge at {difficulty} level.",
            })
            skill_idx += 1
            template_idx += 1
        if candidate_projects:
            for i, project in enumerate(candidate_projects[:2]):
                if len(questions) >= num_questions:
                    break
                template = RESUME_QUESTION_TEMPLATES[i % len(RESUME_QUESTION_TEMPLATES)]
                skill = candidate_skills[0] if candidate_skills else "your expertise"
                other = candidate_skills[1] if len(candidate_skills) > 1 else "related tools"
                questions.append({
                    "question": template.format(project=project, skill=skill, other_skill=other),
                    "type": "resume",
                    "target_skill": skill,
                    "job_requirement": "",
                    "rationale": f"Probing experience in project '{project}'.",
                })
        return questions[:num_questions]

    @staticmethod
    def _parse_json_response(content: str) -> List[Dict[str, Any]]:
        content = content.strip()
        if content.startswith("```"):
            lines = content.split("\n")
            lines = [l for l in lines if not l.strip().startswith("```")]
            content = "\n".join(lines)
        try:
            parsed = json.loads(content)
            if isinstance(parsed, list):
                return parsed
            if isinstance(parsed, dict) and "questions" in parsed:
                return parsed["questions"]
            return []
        except json.JSONDecodeError:
            logger.warning("Could not parse LLM JSON response")
            return []
