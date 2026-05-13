"""Unit tests for the updated 4-signal confidence model."""

import pytest
from modules.evaluation.confidence_model import (
    calculate_confidence,
    calculate_fluency_score,
    aggregate_confidence_timeline,
    _score_to_level,
)


class TestCalculateConfidence:
    def test_all_high_signals_give_high_score(self):
        result = calculate_confidence(
            facial_confidence=90.0,
            speech_emotion_confidence=85.0,
            acoustic_confidence=80.0,
            fluency_score=88.0,
        )
        assert result["combined_score"] >= 80.0
        assert result["confidence_level"] in {"very_confident", "confident"}

    def test_all_low_signals_give_low_score(self):
        result = calculate_confidence(
            facial_confidence=10.0,
            speech_emotion_confidence=15.0,
            acoustic_confidence=20.0,
            fluency_score=10.0,
        )
        assert result["combined_score"] <= 30.0

    def test_score_clamped_to_100(self):
        result = calculate_confidence(100, 100, 100, 100)
        assert result["combined_score"] <= 100.0

    def test_score_clamped_to_0(self):
        result = calculate_confidence(0, 0, 0, 0)
        assert result["combined_score"] >= 0.0

    def test_legacy_voice_confidence_parameter(self):
        """voice_confidence (old API) should map to acoustic_confidence."""
        result = calculate_confidence(
            facial_confidence=70.0,
            voice_confidence=60.0,  # legacy
            fluency_score=55.0,
        )
        assert "combined_score" in result
        assert result["acoustic_score"] == 60.0

    def test_custom_weights_applied(self):
        custom_w = {
            "facial": 1.0,
            "speech_emotion": 0.0,
            "acoustic": 0.0,
            "fluency": 0.0,
        }
        result = calculate_confidence(
            facial_confidence=80.0,
            speech_emotion_confidence=0.0,
            acoustic_confidence=0.0,
            fluency_score=0.0,
            weights=custom_w,
        )
        assert result["combined_score"] == pytest.approx(80.0, abs=0.1)

    def test_result_has_all_keys(self):
        result = calculate_confidence(50, 50, 50, 50)
        expected_keys = {
            "combined_score", "facial_score", "speech_emotion_score",
            "acoustic_score", "fluency_score", "weights_used", "confidence_level"
        }
        assert expected_keys.issubset(set(result.keys()))


class TestCalculateFluency:
    def test_ideal_speed_gives_high_score(self):
        score = calculate_fluency_score(140, 0.15, False)
        assert score >= 70.0

    def test_hesitation_reduces_score(self):
        score_no_hes = calculate_fluency_score(140, 0.15, False)
        score_with_hes = calculate_fluency_score(140, 0.15, True)
        assert score_with_hes < score_no_hes

    def test_high_pause_ratio_reduces_score(self):
        score = calculate_fluency_score(120, 0.75, False)
        assert score <= 45.0


class TestAggregateTimeline:
    def test_empty_timeline_returns_defaults(self):
        result = aggregate_confidence_timeline([])
        assert result["average"] == 50.0
        assert result["trend"] == "stable"

    def test_improving_trend_detected(self):
        timeline = [
            {"combined_score": 40.0},
            {"combined_score": 45.0},
            {"combined_score": 65.0},
            {"combined_score": 75.0},
        ]
        result = aggregate_confidence_timeline(timeline)
        assert result["trend"] == "improving"

    def test_declining_trend_detected(self):
        timeline = [
            {"combined_score": 80.0},
            {"combined_score": 70.0},
            {"combined_score": 50.0},
            {"combined_score": 40.0},
        ]
        result = aggregate_confidence_timeline(timeline)
        assert result["trend"] == "declining"
