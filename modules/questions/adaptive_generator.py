"""Adaptive interview question generator.

Uses mistralai/Mistral-7B-Instruct-v0.3 via HuggingFace Inference API
(free tier) or a local transformers pipeline as fallback.

Model card: https://huggingface.co/mistralai/Mistral-7B-Instruct-v0.3

Prompt strategy
---------------
Each call receives:
  - structured candidate profile (from NER parser)
  - retrieved context chunks (from Chroma RAG)
  - previous question + candidate answer
  - multimodal confidence/emotion state
  - target role + difficulty level

Model is asked to return structured JSON so outputs can be validated
before being rendered in the interview UI.
"""

from __future__ import annotations

import json
import logging
import os
import re
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are an expert technical interview agent. "
    "You generate precise, targeted interview questions in JSON format. "
    "Always return valid JSON and nothing else."
)

QUESTION_PROMPT_TEMPLATE = """\
Candidate profile:
{profile}

Relevant context from resume / JD:
{context}

Previous question asked:
{previous_question}

Candidate's answer:
{answer}

Multimodal confidence state:
{confidence_state}

Target role: {role}
Current difficulty: {difficulty}

Based on all the above, generate the next interview question.
Return a JSON object with these exact keys:
  next_question    (string)
  reason           (string, 1 sentence)
  difficulty       ("easy" | "medium" | "hard")
  skill_target     (string)
  followup_type    ("deeper" | "clarify" | "new_topic" | "behavioural")
"""


def build_prompt(
    profile: Dict[str, Any],
    context_chunks: List[str],
    previous_question: str,
    answer: str,
    confidence_state: str,
    role: str = "Software Engineer",
    difficulty: str = "medium",
) -> str:
    return QUESTION_PROMPT_TEMPLATE.format(
        profile=json.dumps(profile, ensure_ascii=False, indent=2)[:2_500],
        context="\n".join(context_chunks[:5])[:2_000],
        previous_question=previous_question,
        answer=answer,
        confidence_state=confidence_state,
        role=role,
        difficulty=difficulty,
    )


class MistralAdaptiveGenerator:
    """Adaptive question generator backed by Mistral-7B-Instruct-v0.3.

    Priority order:
      1. HuggingFace Inference API (HF_TOKEN env var)
      2. Local transformers pipeline (requires ~14 GB VRAM or CPU with 4-bit)
      3. Template fallback (when neither is available)
    """

    def __init__(
        self,
        hf_token: Optional[str] = None,
        model_name: str = "mistralai/Mistral-7B-Instruct-v0.3",
        use_local: bool = False,
    ) -> None:
        self.model_name = model_name
        self.hf_token = hf_token or os.getenv("HF_TOKEN", "")
        self.use_local = use_local
        self._local_pipe = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate(
        self,
        profile: Dict[str, Any],
        context_chunks: List[str],
        previous_question: str,
        answer: str,
        confidence_state: str,
        role: str = "Software Engineer",
        difficulty: str = "medium",
    ) -> Dict[str, Any]:
        """Return a validated adaptive question dict."""
        prompt = build_prompt(
            profile, context_chunks, previous_question,
            answer, confidence_state, role, difficulty,
        )
        raw = self._call_model(prompt)
        return self._parse_output(raw, difficulty)

    # ------------------------------------------------------------------
    # Model backends
    # ------------------------------------------------------------------

    def _call_model(self, prompt: str) -> str:
        if self.hf_token and not self.use_local:
            return self._call_inference_api(prompt)
        if self.use_local:
            return self._call_local_pipeline(prompt)
        logger.warning("No HF_TOKEN set and use_local=False. Using template fallback.")
        return self._template_fallback()

    def _call_inference_api(self, prompt: str) -> str:
        """Call HuggingFace Inference API (free tier)."""
        import requests  # noqa: PLC0415
        url = f"https://api-inference.huggingface.co/models/{self.model_name}"
        headers = {"Authorization": f"Bearer {self.hf_token}"}
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        payload = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": 512,
                "temperature": 0.4,
                "return_full_text": False,
            },
        }
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            if isinstance(data, list) and data:
                return data[0].get("generated_text", "")
        except Exception as exc:  # noqa: BLE001
            logger.warning("HF Inference API error: %s", exc)
        return self._template_fallback()

    def _call_local_pipeline(self, prompt: str) -> str:
        """Run model locally via transformers pipeline."""
        if self._local_pipe is None:
            from transformers import pipeline  # noqa: PLC0415
            logger.info("Loading local pipeline for %s", self.model_name)
            self._local_pipe = pipeline(
                "text-generation",
                model=self.model_name,
                device_map="auto",
                max_new_tokens=512,
            )
        out = self._local_pipe(prompt, return_full_text=False)
        return out[0]["generated_text"] if out else self._template_fallback()

    # ------------------------------------------------------------------
    # Output parsing
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_output(raw: str, fallback_difficulty: str) -> Dict[str, Any]:
        """Extract and validate JSON from model output."""
        json_match = re.search(r"\{[^{}]*\}", raw, re.DOTALL)
        if json_match:
            try:
                data = json.loads(json_match.group())
                required = {"next_question", "reason", "difficulty", "skill_target", "followup_type"}
                if required.issubset(data.keys()):
                    return data
            except json.JSONDecodeError:
                pass
        return {
            "next_question": raw.strip() or "Can you elaborate on your experience?",
            "reason": "Parsed from free-form model output.",
            "difficulty": fallback_difficulty,
            "skill_target": "general",
            "followup_type": "clarify",
        }

    @staticmethod
    def _template_fallback() -> str:
        return json.dumps({
            "next_question": "Can you walk me through a challenging technical problem you solved recently?",
            "reason": "Template fallback — HF token not configured.",
            "difficulty": "medium",
            "skill_target": "problem-solving",
            "followup_type": "new_topic",
        })
