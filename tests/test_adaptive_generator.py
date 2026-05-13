"""Unit tests for modules/questions/adaptive_generator.py.

HuggingFace Inference API and local pipeline are mocked.
"""

import json
from unittest.mock import MagicMock, patch

import pytest

from modules.questions.adaptive_generator import (
    MistralAdaptiveGenerator,
    build_prompt,
)

SAMPLE_PROFILE = {
    "name": "Ujjawal Ranjan",
    "skills": ["python", "fastapi", "mongodb"],
    "organisations": ["Infosys"],
}

VALID_JSON_OUTPUT = json.dumps({
    "next_question": "How do you handle concurrency in FastAPI?",
    "reason": "Candidate mentioned FastAPI in their resume.",
    "difficulty": "medium",
    "skill_target": "fastapi",
    "followup_type": "deeper",
})


def test_build_prompt_contains_profile():
    prompt = build_prompt(
        SAMPLE_PROFILE, ["context chunk"], "Tell me about yourself.",
        "I am a Python developer.", "confident",
    )
    assert "Ujjawal Ranjan" in prompt
    assert "context chunk" in prompt
    assert "Tell me about yourself" in prompt


def test_generate_returns_dict_with_hf_api():
    gen = MistralAdaptiveGenerator(hf_token="fake_token")
    with patch.object(gen, "_call_inference_api", return_value=VALID_JSON_OUTPUT):
        result = gen.generate(
            SAMPLE_PROFILE, ["context chunk"],
            "What is Python?", "It is a language.", "confident",
        )
    assert "next_question" in result
    assert "skill_target" in result
    assert result["difficulty"] == "medium"


def test_template_fallback_is_valid_json():
    raw = MistralAdaptiveGenerator._template_fallback()
    parsed = json.loads(raw)
    assert "next_question" in parsed


def test_parse_output_handles_malformed():
    result = MistralAdaptiveGenerator._parse_output("This is not JSON at all.", "easy")
    assert "next_question" in result
    assert result["difficulty"] == "easy"


def test_generate_uses_fallback_when_no_token():
    gen = MistralAdaptiveGenerator(hf_token="")
    result = gen.generate(
        SAMPLE_PROFILE, [], "Question?", "Answer.", "neutral",
    )
    assert "next_question" in result
