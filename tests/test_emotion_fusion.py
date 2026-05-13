"""Unit tests for the multimodal emotion fusion layer."""

import pytest
from modules.voice.emotion_fusion import (
    fuse_emotions,
    _score_to_level,
    _generate_recommendation,
    DEFAULT_WEIGHTS,
)


# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def happy_facial():
    return {"dominant_emotion": "happy", "confidence": 85.0}


@pytest.fixture
def nervous_facial():
    return {"dominant_emotion": "fearful", "confidence": 20.0}


@pytest.fixture
def neutral_voice():
    return {
        "speechbrain": {"emotion": "neutral", "score": 0.8, "confidence_impact": 5},
        "confidence_score": 60.0,
        "emotion_label": "neutral",
        "pause_ratio": 0.2,
        "hesitation_detected": False,
    }


@pytest.fixture
def nervous_voice():
    return {
        "speechbrain": {"emotion": "fearful", "score": 0.75, "confidence_impact": -20},
        "confidence_score": 30.0,
        "emotion_label": "nervous",
        "pause_ratio": 0.65,
        "hesitation_detected": True,
    }


# ── Tests ─────────────────────────────────────────────────────────────────────

class TestFuseEmotions:
    def test_returns_required_keys(self, happy_facial, neutral_voice):
        result = fuse_emotions(happy_facial, neutral_voice, fluency_score=70.0)
        required = {
            "fused_confidence", "confidence_level", "dominant_emotion",
            "emotion_agreement", "agreement_bonus", "signal_breakdown",
            "weights_used", "recommendation",
        }
        assert required.issubset(set(result.keys()))

    def test_confident_signals_give_high_score(self, happy_facial, neutral_voice):
        result = fuse_emotions(happy_facial, neutral_voice, fluency_score=75.0)
        assert result["fused_confidence"] >= 60.0

    def test_nervous_signals_give_low_score(self, nervous_facial, nervous_voice):
        result = fuse_emotions(nervous_facial, nervous_voice, fluency_score=30.0)
        assert result["fused_confidence"] <= 50.0

    def test_score_clamped_0_to_100(self, happy_facial, neutral_voice):
        result = fuse_emotions(happy_facial, neutral_voice, fluency_score=100.0)
        assert 0.0 <= result["fused_confidence"] <= 100.0

    def test_agreement_bonus_applied_when_emotions_match(self, happy_facial, neutral_voice):
        result = fuse_emotions(happy_facial, neutral_voice, fluency_score=50.0)
        assert result["emotion_agreement"] is True
        assert result["agreement_bonus"] == 5.0

    def test_agreement_penalty_when_emotions_conflict(self, happy_facial, nervous_voice):
        result = fuse_emotions(happy_facial, nervous_voice, fluency_score=50.0)
        assert result["emotion_agreement"] is False
        assert result["agreement_bonus"] == -3.0

    def test_custom_weights_applied(self, happy_facial, neutral_voice):
        custom_w = {"facial": 1.0, "speech_emotion": 0.0, "acoustic": 0.0, "fluency": 0.0}
        result = fuse_emotions(
            happy_facial, neutral_voice, fluency_score=0.0, weights=custom_w
        )
        # With facial=1.0 weight and facial_confidence=85, raw ≈ 85 + bonus
        assert result["fused_confidence"] >= 80.0

    def test_invalid_weights_raise_error(self, happy_facial, neutral_voice):
        bad_weights = {"facial": 0.5, "speech_emotion": 0.5, "acoustic": 0.5, "fluency": 0.5}
        with pytest.raises(ValueError, match="sum to 1.0"):
            fuse_emotions(happy_facial, neutral_voice, weights=bad_weights)


class TestScoreToLevel:
    def test_very_confident(self):
        assert _score_to_level(85.0) == "very_confident"

    def test_confident(self):
        assert _score_to_level(70.0) == "confident"

    def test_moderate(self):
        assert _score_to_level(55.0) == "moderate"

    def test_uncertain(self):
        assert _score_to_level(40.0) == "uncertain"

    def test_low_confidence(self):
        assert _score_to_level(20.0) == "low_confidence"


class TestRecommendation:
    def test_high_score_positive_message(self):
        msg = _generate_recommendation(80.0, "happy", True)
        assert "Great" in msg or "maintain" in msg.lower()

    def test_low_score_actionable_feedback(self):
        msg = _generate_recommendation(30.0, "fearful", False)
        assert len(msg) > 20  # Should have a real suggestion
