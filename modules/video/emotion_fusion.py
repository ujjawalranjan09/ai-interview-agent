"""Multimodal emotion fusion — combines facial (DeepFace) + audio (SpeechBrain) signals.

This is the new "confidence score" layer that sits above both the video and
voice modules.  It replaces the old approach of trusting either module alone.

Fusion strategy
---------------
We use a simple weighted average with configurable weights.  Defaults reflect
empirical research showing audio is a stronger indicator of interview nerves
than facial expression alone:

  final_score = w_audio * audio_score + w_face * face_score

where:
  - ``audio_score``  comes from ``voice_emotion.analyze_voice_emotion()``
  - ``face_score``   comes from ``video_emotion.analyze_video_emotion()``

Emotion label is resolved by majority vote across modalities, with audio
preferred when scores are tied (audio is more reliable for remote interviews).

Public API
----------
:func:`fuse_emotions`         — main entry, accepts dicts from each module
:func:`fuse_from_files`       — convenience: takes file paths, runs both modules
:func:`get_interview_verdict` — convert fused score to human verdict string
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Default modality weights (audio-biased, per research literature)
DEFAULT_AUDIO_WEIGHT: float = 0.60
DEFAULT_FACE_WEIGHT:  float = 0.40

# Map emotion labels to a numeric confidence value for scoring
_EMOTION_CONFIDENCE_MAP: Dict[str, float] = {
    "confident":  80.0,
    "excited":    75.0,
    "calm":       70.0,
    "neutral":    55.0,
    "uncertain":  35.0,
    "nervous":    30.0,
    "anxious":    30.0,
    "sad":        30.0,
    "angry":      35.0,
    "fear":       28.0,
    "disgust":    35.0,
    "surprise":   55.0,
    "happy":      75.0,
}


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class FusedEmotionResult:
    """Full multimodal emotion analysis result."""

    # Fused scores
    confidence_score: float          # 0–100 final blended score
    emotion_label: str               # dominant emotion string
    verdict: str                     # interview verdict (see get_interview_verdict)

    # Per-modality raw scores
    audio_confidence: float          # 0–100
    face_confidence: float           # 0–100
    audio_emotion: str
    face_emotion: str

    # SpeechBrain-specific
    sb_emotion: Optional[str] = None    # raw SpeechBrain label (e.g. "hap")
    sb_scores:  Dict[str, float] = field(default_factory=dict)
    analysis_mode: str = "unknown"      # "speechbrain" | "librosa" | "face_only" etc.

    # Additional acoustic / facial metadata (pass-through)
    hesitation_detected: bool = False
    pause_ratio: float = 0.0
    speaking_speed: float = 120.0
    pitch_std: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "confidence_score":    round(self.confidence_score, 1),
            "emotion_label":       self.emotion_label,
            "verdict":             self.verdict,
            "audio_confidence":    round(self.audio_confidence, 1),
            "face_confidence":     round(self.face_confidence, 1),
            "audio_emotion":       self.audio_emotion,
            "face_emotion":        self.face_emotion,
            "sb_emotion":          self.sb_emotion,
            "sb_scores":           self.sb_scores,
            "analysis_mode":       self.analysis_mode,
            "hesitation_detected": self.hesitation_detected,
            "pause_ratio":         round(self.pause_ratio, 3),
            "speaking_speed":      round(self.speaking_speed, 1),
            "pitch_std":           round(self.pitch_std, 2),
        }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def fuse_emotions(
    audio_result: Dict[str, Any],
    face_result:  Optional[Dict[str, Any]] = None,
    audio_weight: float = DEFAULT_AUDIO_WEIGHT,
    face_weight:  float = DEFAULT_FACE_WEIGHT,
) -> FusedEmotionResult:
    """Fuse audio and optional facial emotion analysis results.

    Args:
        audio_result:  Output dict from ``analyze_voice_emotion()``.
        face_result:   Output dict from ``analyze_video_emotion()`` (optional).
                       When None, only audio signal is used (audio_weight = 1.0).
        audio_weight:  Weight for audio modality (0–1).  Default 0.60.
        face_weight:   Weight for face  modality (0–1).  Default 0.40.

    Returns:
        :class:`FusedEmotionResult` with all fields populated.
    """
    audio_conf  = float(audio_result.get("confidence_score", 50.0))
    audio_emot  = str(audio_result.get("emotion_label", "neutral"))

    if face_result is not None:
        face_conf = float(face_result.get("confidence_score", 50.0))
        face_emot = str(face_result.get("dominant_emotion",
                        face_result.get("emotion_label", "neutral")))
        eff_audio_w = audio_weight / (audio_weight + face_weight)   # normalise
        eff_face_w  = face_weight  / (audio_weight + face_weight)
    else:
        face_conf = 50.0
        face_emot = "neutral"
        eff_audio_w, eff_face_w = 1.0, 0.0

    blended_score = eff_audio_w * audio_conf + eff_face_w * face_conf
    dominant_emotion = _resolve_dominant_emotion(
        audio_emot, audio_conf, face_emot, face_conf, eff_audio_w
    )

    # Determine analysis mode
    sb_mode = str(audio_result.get("analysis_mode", "librosa"))
    if face_result is not None:
        mode = f"{sb_mode}+face"
    else:
        mode = sb_mode

    return FusedEmotionResult(
        confidence_score    = round(min(100.0, max(0.0, blended_score)), 1),
        emotion_label       = dominant_emotion,
        verdict             = get_interview_verdict(blended_score),
        audio_confidence    = audio_conf,
        face_confidence     = face_conf,
        audio_emotion       = audio_emot,
        face_emotion        = face_emot,
        sb_emotion          = audio_result.get("sb_emotion"),
        sb_scores           = audio_result.get("sb_scores", {}),
        analysis_mode       = mode,
        hesitation_detected = bool(audio_result.get("hesitation_detected", False)),
        pause_ratio         = float(audio_result.get("pause_ratio", 0.0)),
        speaking_speed      = float(audio_result.get("speaking_speed", 120.0)),
        pitch_std           = float(audio_result.get("pitch_std", 0.0)),
    )


def fuse_from_files(
    audio_path: str,
    video_path: Optional[str] = None,
    audio_weight: float = DEFAULT_AUDIO_WEIGHT,
    face_weight:  float = DEFAULT_FACE_WEIGHT,
) -> FusedEmotionResult:
    """Convenience wrapper: run both modules from file paths and fuse.

    Args:
        audio_path:   Path to audio file (WAV/MP3).
        video_path:   Path to video file (MP4/AVI).  Optional.
        audio_weight: Modality weight for audio.
        face_weight:  Modality weight for face.

    Returns:
        :class:`FusedEmotionResult`
    """
    from modules.voice.voice_emotion import analyze_voice_emotion
    audio_result = analyze_voice_emotion(audio_path)

    face_result: Optional[Dict[str, Any]] = None
    if video_path is not None:
        try:
            from modules.video.video_emotion import analyze_video_emotion
            face_result = analyze_video_emotion(video_path)
        except Exception as exc:
            logger.warning("Video emotion analysis failed, using audio only: %s", exc)

    return fuse_emotions(
        audio_result=audio_result,
        face_result=face_result,
        audio_weight=audio_weight,
        face_weight=face_weight,
    )


def get_interview_verdict(score: float) -> str:
    """Convert a 0–100 confidence score to a human-readable interview verdict.

    Args:
        score: Fused confidence score (0–100).

    Returns:
        Verdict string used in reports and UI.
    """
    if score >= 75:
        return "Highly Confident"
    elif score >= 60:
        return "Confident"
    elif score >= 45:
        return "Moderate"
    elif score >= 30:
        return "Nervous"
    return "Highly Nervous"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _resolve_dominant_emotion(
    audio_emotion: str,
    audio_conf:    float,
    face_emotion:  str,
    face_conf:     float,
    audio_weight:  float,
) -> str:
    """Pick the dominant emotion label via weighted vote."""
    if audio_emotion == face_emotion:
        return audio_emotion

    # Convert emotion labels to a numeric value, then weighted vote
    audio_val = _EMOTION_CONFIDENCE_MAP.get(audio_emotion.lower(), 50.0)
    face_val  = _EMOTION_CONFIDENCE_MAP.get(face_emotion.lower(),  50.0)

    audio_weighted = audio_weight * audio_val
    face_weighted  = (1.0 - audio_weight) * face_val

    # Audio wins ties (more reliable for remote/recorded interviews)
    return audio_emotion if audio_weighted >= face_weighted else face_emotion
