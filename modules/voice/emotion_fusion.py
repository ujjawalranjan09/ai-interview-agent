"""Multimodal emotion fusion: facial + speech (SpeechBrain) + librosa acoustics.

This is the core "week 1" upgrade — combining three independent emotion
signals into a single fused score per interview response:

  Signal 1: DeepFace (facial expression from video frames)
  Signal 2: SpeechBrain wav2vec2-IEMOCAP (emotion from audio waveform)
  Signal 3: librosa acoustic features (pitch, energy, pauses, hesitation)

Fusion formula (default weights):
  fused_confidence = 0.40 × facial + 0.35 × speech_emotion + 0.15 × acoustic + 0.10 × fluency

The weights are configurable via the EMOTION_FUSION_WEIGHTS env variable or
direct parameter override.
"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Default fusion weights — must sum to 1.0
DEFAULT_WEIGHTS = {
    "facial": 0.40,       # DeepFace facial emotion confidence
    "speech_emotion": 0.35,  # SpeechBrain wav2vec2 deep emotion
    "acoustic": 0.15,     # librosa acoustic heuristic score
    "fluency": 0.10,      # Speech fluency (pause ratio, WPM)
}

# Emotion agreement bonus: when facial and speech agree, boost confidence
_POSITIVE_EMOTIONS = {"happy", "excited", "confident", "calm", "neutral"}
_NEGATIVE_EMOTIONS = {"angry", "fearful", "frustrated", "sad", "disgusted", "nervous", "uncertain"}


def fuse_emotions(
    facial_result: Dict[str, Any],
    voice_result: Dict[str, Any],
    fluency_score: float = 50.0,
    weights: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    """Fuse facial, speech, and acoustic emotion signals into one score.

    Args:
        facial_result: Output from DeepFace analysis with keys:
            'dominant_emotion', 'emotion' (dict of probabilities),
            'confidence' (0-100 score).
        voice_result: Output from analyze_voice_emotion() with keys:
            'speechbrain' (SpeechBrain result), 'confidence_score',
            'emotion_label', 'pause_ratio', 'hesitation_detected'.
        fluency_score: Pre-computed fluency score (0-100).
        weights: Optional custom weight dict overriding DEFAULT_WEIGHTS.

    Returns:
        Fused emotion result dict with:
            - fused_confidence: Final 0-100 confidence score
            - confidence_level: Human label (very_confident ... low_confidence)
            - dominant_emotion: Most strongly detected emotion
            - emotion_agreement: Whether facial and voice agree
            - agreement_bonus: Points added for emotional consistency
            - signal_breakdown: Per-signal scores used in fusion
            - weights_used: Weights applied
            - recommendation: Actionable feedback string
    """
    w = weights or DEFAULT_WEIGHTS
    _validate_weights(w)

    # ── Extract facial signal ──────────────────────────────────────────
    facial_confidence = float(facial_result.get("confidence", 50.0))
    facial_emotion = str(
        facial_result.get("dominant_emotion", "neutral")
    ).lower()

    # ── Extract speech emotion signal (SpeechBrain) ───────────────────
    sb = voice_result.get("speechbrain", {})
    sb_emotion = sb.get("emotion", "neutral")
    sb_score = float(sb.get("score", 0.5))  # 0-1 model confidence
    sb_impact = float(sb.get("confidence_impact", 0))
    # Convert sb_score (0-1) to 0-100, then apply emotion impact
    speech_emotion_confidence = min(100.0, max(0.0, sb_score * 100 + sb_impact))

    # ── Extract acoustic signal (librosa) ─────────────────────────────
    acoustic_confidence = float(voice_result.get("confidence_score", 50.0))

    # ── Weighted fusion ───────────────────────────────────────────────
    raw_fused = (
        w["facial"] * facial_confidence
        + w["speech_emotion"] * speech_emotion_confidence
        + w["acoustic"] * acoustic_confidence
        + w["fluency"] * fluency_score
    )

    # ── Agreement bonus (+5 if facial & speech agree on pos/neg) ─────
    facial_positive = facial_emotion in _POSITIVE_EMOTIONS
    speech_positive = sb_emotion in _POSITIVE_EMOTIONS
    agreement = facial_positive == speech_positive
    agreement_bonus = 5.0 if agreement else -3.0
    fused = min(100.0, max(0.0, raw_fused + agreement_bonus))

    # ── Dominant emotion (highest-confidence signal wins) ────────────
    signal_emotions = [
        (facial_confidence, facial_emotion, "facial"),
        (speech_emotion_confidence, sb_emotion, "speechbrain"),
        (acoustic_confidence, voice_result.get("emotion_label", "neutral"), "acoustic"),
    ]
    dominant_source = max(signal_emotions, key=lambda x: x[0])
    dominant_emotion = dominant_source[1]

    result = {
        "fused_confidence": round(fused, 1),
        "confidence_level": _score_to_level(fused),
        "dominant_emotion": dominant_emotion,
        "dominant_source": dominant_source[2],
        "emotion_agreement": agreement,
        "agreement_bonus": agreement_bonus,
        "signal_breakdown": {
            "facial_confidence": round(facial_confidence, 1),
            "facial_emotion": facial_emotion,
            "speech_emotion_confidence": round(speech_emotion_confidence, 1),
            "speech_emotion": sb_emotion,
            "acoustic_confidence": round(acoustic_confidence, 1),
            "acoustic_emotion": voice_result.get("emotion_label", "neutral"),
            "fluency_score": round(fluency_score, 1),
        },
        "weights_used": w,
        "recommendation": _generate_recommendation(fused, dominant_emotion, agreement),
    }

    logger.info(
        f"Emotion fusion: fused={fused:.1f} | facial={facial_emotion}({facial_confidence:.0f}) "
        f"| speech={sb_emotion}({speech_emotion_confidence:.0f}) "
        f"| acoustic={acoustic_confidence:.0f} | agreement={agreement}"
    )
    return result


def _validate_weights(w: Dict[str, float]) -> None:
    required = {"facial", "speech_emotion", "acoustic", "fluency"}
    missing = required - set(w.keys())
    if missing:
        raise ValueError(f"Missing fusion weight keys: {missing}")
    total = sum(w.values())
    if not (0.99 <= total <= 1.01):
        raise ValueError(f"Fusion weights must sum to 1.0, got {total:.3f}")


def _score_to_level(score: float) -> str:
    if score >= 80:
        return "very_confident"
    elif score >= 65:
        return "confident"
    elif score >= 50:
        return "moderate"
    elif score >= 35:
        return "uncertain"
    return "low_confidence"


def _generate_recommendation(score: float, emotion: str, agreement: bool) -> str:
    """Generate actionable feedback based on fusion result."""
    if score >= 75:
        return "Great composure — maintain this energy throughout the interview."
    elif score >= 60:
        if emotion in {"nervous", "fearful"}:
            return "Slight nervousness detected. Take a breath before answering — your content is strong."
        return "Solid confidence. Try to add a bit more enthusiasm in your delivery."
    elif score >= 45:
        if not agreement:
            return "Mixed signals between face and voice. Try to align your body language with your words."
        return "Moderate confidence. Slow down slightly and avoid filler pauses."
    else:
        return "Low confidence detected. Practice power posture before interviews and speak more slowly and clearly."
