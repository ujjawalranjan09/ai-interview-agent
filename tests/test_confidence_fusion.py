"""Unit tests for modules/evaluation/confidence_fusion.py."""

import pytest

from modules.evaluation.confidence_fusion import (
    AGREEMENT_BONUS,
    CONFLICT_PENALTY,
    ConfidenceTimeline,
    FusionInput,
    compute_confidence,
)


def _make_input(**kwargs) -> FusionInput:
    defaults = dict(
        facial_score=60.0,
        facial_emotion="neutral",
        speech_emotion_score=60.0,
        speech_emotion_label="neutral",
        acoustic_score=60.0,
        text_sentiment_score=60.0,
        question_index=0,
        answer_text="I used Python to build the API.",
    )
    defaults.update(kwargs)
    return FusionInput(**defaults)


def test_basic_fusion_score():
    inp = _make_input()
    result = compute_confidence(inp)
    assert 0.0 <= result.confidence_score <= 100.0


def test_agreement_bonus_applied():
    inp = _make_input(facial_emotion="happy", speech_emotion_label="excited")
    result = compute_confidence(inp)
    assert result.emotion_agreement == "agree"
    assert result.agreement_adjustment == AGREEMENT_BONUS


def test_conflict_penalty_applied():
    inp = _make_input(facial_emotion="happy", speech_emotion_label="angry")
    result = compute_confidence(inp)
    assert result.emotion_agreement == "conflict"
    assert result.agreement_adjustment == CONFLICT_PENALTY


def test_neutral_no_adjustment():
    inp = _make_input(facial_emotion="neutral", speech_emotion_label="angry")
    result = compute_confidence(inp)
    assert result.emotion_agreement == "neutral"
    assert result.agreement_adjustment == 0.0


def test_score_clamped_to_100():
    inp = _make_input(
        facial_score=100.0, speech_emotion_score=100.0,
        acoustic_score=100.0, text_sentiment_score=100.0,
        facial_emotion="happy", speech_emotion_label="excited",
    )
    result = compute_confidence(inp)
    assert result.confidence_score <= 100.0


def test_score_clamped_to_0():
    inp = _make_input(
        facial_score=0.0, speech_emotion_score=0.0,
        acoustic_score=0.0, text_sentiment_score=0.0,
        facial_emotion="angry", speech_emotion_label="happy",
    )
    result = compute_confidence(inp)
    assert result.confidence_score >= 0.0


def test_label_confident():
    inp = _make_input(
        facial_score=80.0, speech_emotion_score=80.0,
        acoustic_score=80.0, text_sentiment_score=80.0,
    )
    result = compute_confidence(inp)
    assert result.label == "confident"


def test_label_nervous():
    inp = _make_input(
        facial_score=20.0, speech_emotion_score=20.0,
        acoustic_score=20.0, text_sentiment_score=20.0,
    )
    result = compute_confidence(inp)
    assert result.label == "nervous"


class TestConfidenceTimeline:
    def test_average_computed(self):
        tl = ConfidenceTimeline()
        for score in [50.0, 60.0, 70.0]:
            inp = _make_input(facial_score=score, speech_emotion_score=score,
                              acoustic_score=score, text_sentiment_score=score)
            tl.add(compute_confidence(inp))
        assert 50.0 <= tl.average <= 70.0

    def test_trend_improving(self):
        tl = ConfidenceTimeline()
        scores = [30.0, 35.0, 38.0, 70.0, 75.0, 80.0]
        for s in scores:
            inp = _make_input(facial_score=s, speech_emotion_score=s,
                              acoustic_score=s, text_sentiment_score=s)
            tl.add(compute_confidence(inp))
        assert tl.trend == "improving"

    def test_trend_declining(self):
        tl = ConfidenceTimeline()
        scores = [80.0, 78.0, 76.0, 40.0, 38.0, 35.0]
        for s in scores:
            inp = _make_input(facial_score=s, speech_emotion_score=s,
                              acoustic_score=s, text_sentiment_score=s)
            tl.add(compute_confidence(inp))
        assert tl.trend == "declining"

    def test_summary_keys(self):
        tl = ConfidenceTimeline()
        inp = _make_input()
        tl.add(compute_confidence(inp))
        s = tl.summary()
        assert "average_confidence" in s
        assert "trend" in s
        assert "agreement_counts" in s
