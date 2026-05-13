"""Voice emotion analysis: librosa acoustic features + SpeechBrain HF model.

This module combines two complementary approaches:
1. SpeechBrain wav2vec2-IEMOCAP (HuggingFace) — deep-learning emotion from waveform
2. librosa acoustic features — pitch, energy, pauses, hesitations

The results are designed to feed into emotion_fusion.py for multimodal scoring.
"""

import logging
import os
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


def analyze_voice_emotion(audio_path: str, use_speechbrain: bool = True) -> Dict[str, Any]:
    """Analyze emotional features from voice audio.

    Runs librosa acoustic analysis and optionally the SpeechBrain
    wav2vec2 emotion classifier for a richer signal.

    Args:
        audio_path: Path to the audio file.
        use_speechbrain: Whether to run the HuggingFace SpeechBrain model.
            Falls back gracefully if model not loaded.

    Returns:
        Dictionary with voice emotion features:
            - pitch_mean, pitch_std: Fundamental frequency stats
            - energy_mean, energy_std: RMS energy stats
            - spectral_centroid: Spectral brightness
            - zcr_mean: Zero-crossing rate (voice quality)
            - speaking_speed: Estimated words per minute
            - pause_ratio: Fraction of audio that is silence
            - hesitation_detected: Whether multiple short pauses found
            - short_pauses: Count of hesitation pauses
            - duration: Audio duration in seconds
            - emotion_label: Inferred emotion string
            - confidence_score: Acoustic confidence score (0-100)
            - speechbrain: SpeechBrain result dict (if use_speechbrain=True)
    """
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    try:
        import librosa
        import numpy as np
    except ImportError:
        logger.warning("librosa not available, returning default values")
        return _default_voice_features()

    result = {}

    # ── 1. SpeechBrain deep emotion classification ──────────────────────
    sb_result = None
    if use_speechbrain:
        try:
            from modules.voice.speechbrain_emotion import classify_emotion
            sb_result = classify_emotion(audio_path)
            result["speechbrain"] = sb_result
            logger.info(
                f"SpeechBrain emotion: {sb_result.get('emotion')} "
                f"(score={sb_result.get('score', 0):.3f})"
            )
        except Exception as e:
            logger.warning(f"SpeechBrain classification skipped: {e}")
            result["speechbrain"] = {"emotion": "neutral", "score": 0.5, "error": str(e)}

    # ── 2. librosa acoustic feature extraction ───────────────────────────
    try:
        y, sr = librosa.load(audio_path, sr=None)

        if len(y) == 0:
            return _default_voice_features()

        # Pitch via pyin
        f0, voiced_flag, _ = librosa.pyin(
            y,
            fmin=librosa.note_to_hz("C2"),
            fmax=librosa.note_to_hz("C7"),
            sr=sr,
        )
        f0_clean = f0[~np.isnan(f0)] if f0 is not None else np.array([])
        pitch_mean = float(np.mean(f0_clean)) if len(f0_clean) > 0 else 0.0
        pitch_std = float(np.std(f0_clean)) if len(f0_clean) > 0 else 0.0

        # Energy (RMS)
        rms = librosa.feature.rms(y=y)[0]
        energy_mean = float(np.mean(rms))
        energy_std = float(np.std(rms))

        # Spectral centroid (brightness)
        spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
        spectral_mean = float(np.mean(spectral_centroid))

        # Zero crossing rate
        zcr = librosa.feature.zero_crossing_rate(y)[0]
        zcr_mean = float(np.mean(zcr))

        # Pause detection
        rms_normalized = rms / (np.max(rms) + 1e-8)
        silence_threshold = 0.05
        is_silent = rms_normalized < silence_threshold
        pause_ratio = float(np.mean(is_silent))

        # Hesitation: multiple short pauses (0.1s – 0.5s)
        diff = np.diff(is_silent.astype(int))
        pause_starts = np.where(diff == 1)[0]
        pause_ends = np.where(diff == -1)[0]
        frame_duration = len(y) / sr / len(rms)
        short_pauses = 0
        for start, end in zip(pause_starts, pause_ends):
            if 0.1 < (end - start) * frame_duration < 0.5:
                short_pauses += 1
        hesitation_detected = short_pauses >= 3

        # Speaking rate estimate
        duration = len(y) / sr
        voiced_ratio = float(np.mean(voiced_flag)) if voiced_flag is not None else 0.5
        estimated_wpm = max(60, min(200, 80 + voiced_ratio * 100))

        # Acoustic confidence score
        confidence_score = _calculate_voice_confidence(
            pitch_mean=pitch_mean,
            pitch_std=pitch_std,
            energy_mean=energy_mean,
            energy_std=energy_std,
            pause_ratio=pause_ratio,
            hesitation_detected=hesitation_detected,
            zcr_mean=zcr_mean,
        )

        # Prefer SpeechBrain emotion label; fall back to heuristic
        if sb_result and not sb_result.get("error"):
            emotion_label = sb_result["emotion"]
            # Blend SpeechBrain confidence impact into acoustic score
            confidence_score = min(
                100.0,
                max(0.0, confidence_score + sb_result.get("confidence_impact", 0))
            )
        else:
            emotion_label = _infer_emotion(
                pitch_mean=pitch_mean,
                pitch_std=pitch_std,
                energy_mean=energy_mean,
                pause_ratio=pause_ratio,
            )

        result.update({
            "pitch_mean": round(pitch_mean, 2),
            "pitch_std": round(pitch_std, 2),
            "energy_mean": round(energy_mean, 6),
            "energy_std": round(energy_std, 6),
            "spectral_centroid": round(spectral_mean, 2),
            "zcr_mean": round(zcr_mean, 6),
            "speaking_speed": round(estimated_wpm, 1),
            "pause_ratio": round(pause_ratio, 3),
            "hesitation_detected": hesitation_detected,
            "short_pauses": short_pauses,
            "emotion_label": emotion_label,
            "confidence_score": round(confidence_score, 1),
            "duration": round(duration, 2),
        })
        return result

    except Exception as e:
        logger.error(f"Voice emotion analysis failed: {e}")
        return _default_voice_features(error=str(e))


def _calculate_voice_confidence(
    pitch_mean: float,
    pitch_std: float,
    energy_mean: float,
    energy_std: float,
    pause_ratio: float,
    hesitation_detected: bool,
    zcr_mean: float,
) -> float:
    score = 50.0
    if 20 < pitch_std < 100:
        score += 10
    elif pitch_std > 150:
        score -= 5
    if energy_mean > 0.02:
        score += 10
    elif energy_mean < 0.005:
        score -= 10
    if pause_ratio < 0.3:
        score += 10
    elif pause_ratio > 0.6:
        score -= 15
    if hesitation_detected:
        score -= 15
    if zcr_mean > 0.15:
        score -= 5
    return max(0.0, min(100.0, score))


def _infer_emotion(
    pitch_mean: float,
    pitch_std: float,
    energy_mean: float,
    pause_ratio: float,
) -> str:
    if energy_mean > 0.03 and pitch_std > 50:
        return "excited" if pitch_mean > 200 else "confident"
    elif energy_mean < 0.01 and pause_ratio > 0.5:
        return "nervous"
    elif pitch_std < 20 and energy_mean < 0.015:
        return "calm"
    elif energy_mean > 0.02:
        return "neutral"
    return "uncertain"


def _default_voice_features(error: str = "") -> Dict[str, Any]:
    return {
        "pitch_mean": 0.0,
        "pitch_std": 0.0,
        "energy_mean": 0.0,
        "energy_std": 0.0,
        "spectral_centroid": 0.0,
        "zcr_mean": 0.0,
        "speaking_speed": 120.0,
        "pause_ratio": 0.0,
        "hesitation_detected": False,
        "short_pauses": 0,
        "emotion_label": "neutral",
        "confidence_score": 50.0,
        "duration": 0.0,
        "speechbrain": {},
        "error": error,
    }
