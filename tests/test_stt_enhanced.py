"""Unit tests for modules/voice/stt_enhanced.py.

Whisper model is mocked — no download needed in CI.
"""

from unittest.mock import MagicMock, patch

import pytest

from modules.voice.stt_enhanced import EnhancedSTT, TranscriptResult, _clean_transcript


MOCK_WHISPER_RESULT = {
    "text": " Um, I basically used Python and like FastAPI to build the API.",
    "language": "en",
    "segments": [
        {"avg_logprob": -0.4, "no_speech_prob": 0.05},
        {"avg_logprob": -0.3, "no_speech_prob": 0.04},
    ],
}


@pytest.fixture()
def stt():
    stt_obj = EnhancedSTT(model_size="base", language="en")
    mock_model = MagicMock()
    mock_model.transcribe.return_value = MOCK_WHISPER_RESULT
    stt_obj._model = mock_model
    return stt_obj


def test_transcribe_returns_transcript_result(stt):
    result = stt.transcribe("fake_audio.wav")
    assert isinstance(result, TranscriptResult)


def test_raw_text_preserved(stt):
    result = stt.transcribe("fake_audio.wav")
    assert "FastAPI" in result.raw_text


def test_fillers_removed(stt):
    result = stt.transcribe("fake_audio.wav")
    assert "um" not in result.cleaned_text.lower()
    assert "basically" not in result.cleaned_text.lower()
    assert "like" not in result.cleaned_text.lower()
    assert "FastAPI" in result.cleaned_text


def test_confidence_flag_high_when_logprob_good(stt):
    result = stt.transcribe("fake_audio.wav")
    assert result.is_confident is True


def test_initial_prompt_contains_tech_terms(stt):
    assert "FastAPI" in stt.initial_prompt
    assert "PyTorch" in stt.initial_prompt


def test_clean_transcript_function():
    raw = "Um I like basically used Python you know for the project"
    cleaned = EnhancedSTT._clean_transcript(raw)
    assert "um" not in cleaned.lower()
    assert "Python" in cleaned
