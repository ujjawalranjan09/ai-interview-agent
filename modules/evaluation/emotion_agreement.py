"""Emotion agreement utilities for the fusion layer.

Provides valence bucketing and agreement detection between
facial (DeepFace) and speech (SpeechBrain) emotion channels.

Used by confidence_fusion.py and the evaluation pipeline.
"""

from __future__ import annotations

POSITIVE_EMOTIONS = frozenset({"happy", "excited", "confident", "joy", "positive"})
NEGATIVE_EMOTIONS = frozenset({"angry", "sad", "fear", "frustrated", "fearful", "nervous", "negative", "disgust"})


def valence(emotion: str) -> str:
    """Bucket a raw emotion label into 'positive', 'negative', or 'neutral'."""
    e = emotion.strip().lower()
    if e in POSITIVE_EMOTIONS:
        return "positive"
    if e in NEGATIVE_EMOTIONS:
        return "negative"
    return "neutral"


def agreement_status(facial_emotion: str, speech_emotion: str) -> str:
    """Return 'agree', 'conflict', or 'neutral' for two emotion labels."""
    fv = valence(facial_emotion)
    sv = valence(speech_emotion)
    if fv == "neutral" or sv == "neutral":
        return "neutral"
    if fv == sv:
        return "agree"
    return "conflict"


def emotion_state_label(confidence_score: float) -> str:
    """Map a numeric confidence score to a human-readable label."""
    if confidence_score >= 70:
        return "confident"
    if confidence_score >= 45:
        return "moderate"
    return "nervous"
