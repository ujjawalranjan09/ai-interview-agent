"""Voice emotion analysis using librosa feature extraction."""

import logging
import tempfile
import os
from typing import Any, Dict

logger = logging.getLogger(__name__)


def analyze_voice_emotion(audio_bytes: bytes) -> Dict[str, Any]:
    try:
        import librosa
        import numpy as np
    except ImportError:
        logger.warning("librosa not available, returning defaults")
        return _default_features()

    tmp = None
    try:
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        tmp.write(audio_bytes)
        tmp.close()

        y, sr = librosa.load(tmp.name, sr=None)
        if len(y) == 0:
            return _default_features()

        f0, voiced_flag, _ = librosa.pyin(y, fmin=librosa.note_to_hz("C2"), fmax=librosa.note_to_hz("C7"), sr=sr)
        f0_clean = f0[~np.isnan(f0)] if f0 is not None else np.array([])
        pitch_mean = float(np.mean(f0_clean)) if len(f0_clean) > 0 else 0.0
        pitch_std = float(np.std(f0_clean)) if len(f0_clean) > 0 else 0.0

        rms = librosa.feature.rms(y=y)[0]
        energy_mean = float(np.mean(rms))

        rms_normalized = rms / (np.max(rms) + 1e-8)
        is_silent = rms_normalized < 0.05
        pause_ratio = float(np.mean(is_silent))

        diff = np.diff(is_silent.astype(int))
        pause_starts = np.where(diff == 1)[0]
        pause_ends = np.where(diff == -1)[0]
        frame_duration = len(y) / sr / len(rms) if len(rms) > 0 else 0
        short_pauses = sum(
            1 for s, e in zip(pause_starts, pause_ends)
            if 0.1 < (e - s) * frame_duration < 0.5
        )
        hesitation_detected = short_pauses >= 3

        duration = len(y) / sr
        voiced_ratio = float(np.mean(voiced_flag)) if voiced_flag is not None else 0.5
        estimated_wpm = max(60, min(200, 80 + voiced_ratio * 100))

        confidence = _calc_confidence(pitch_std, energy_mean, pause_ratio, hesitation_detected)
        emotion_label = _infer_emotion(pitch_mean, pitch_std, energy_mean, pause_ratio)

        return {
            "pitch_mean": round(pitch_mean, 2),
            "pitch_std": round(pitch_std, 2),
            "energy_mean": round(energy_mean, 6),
            "speaking_speed": round(estimated_wpm, 1),
            "pause_ratio": round(pause_ratio, 3),
            "hesitation_detected": hesitation_detected,
            "emotion_label": emotion_label,
            "confidence_score": round(confidence, 1),
            "duration": round(duration, 2),
        }
    except Exception as e:
        logger.error("Voice emotion analysis failed: %s", e)
        return _default_features(error=str(e))
    finally:
        if tmp:
            try:
                os.unlink(tmp.name)
            except OSError:
                pass


def _calc_confidence(pitch_std: float, energy_mean: float, pause_ratio: float, hesitation: bool) -> float:
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
    if hesitation:
        score -= 15
    return max(0.0, min(100.0, score))


def _infer_emotion(pitch_mean: float, pitch_std: float, energy_mean: float, pause_ratio: float) -> str:
    if energy_mean > 0.03 and pitch_std > 50:
        return "excited" if pitch_mean > 200 else "confident"
    elif energy_mean < 0.01 and pause_ratio > 0.5:
        return "nervous"
    elif pitch_std < 20 and energy_mean < 0.015:
        return "calm"
    elif energy_mean > 0.02:
        return "neutral"
    return "uncertain"


def _default_features(error: str = "") -> Dict[str, Any]:
    result = {
        "pitch_mean": 0.0, "pitch_std": 0.0, "energy_mean": 0.0,
        "speaking_speed": 120.0, "pause_ratio": 0.0, "hesitation_detected": False,
        "emotion_label": "neutral", "confidence_score": 50.0, "duration": 0.0,
        "fallback": True,
    }
    if error:
        result["error"] = error
    return result
