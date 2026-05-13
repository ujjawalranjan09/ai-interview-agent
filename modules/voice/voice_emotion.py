"""Voice emotion analysis — SpeechBrain wav2vec2 model + librosa acoustic fallback.

Upgrade from heuristic-only librosa analysis to a real ML model:
  - Primary:  ``speechbrain/emotion-recognition-wav2vec2-IEMOCAP``
              (613K downloads, 4-class: angry / happy / neutral / sad)
  - Fallback: original librosa acoustic heuristics (when speechbrain not installed
              or inference fails) — zero breaking changes for existing callers.

The output dict is a strict superset of the old schema:
  - All original keys are preserved and populated
  - New keys added: ``sb_emotion``, ``sb_scores``, ``sb_confidence``, ``analysis_mode``

Typical usage::

    from modules.voice.voice_emotion import analyze_voice_emotion
    result = analyze_voice_emotion("answer.wav")
    print(result["emotion_label"])   # e.g. "confident"
    print(result["sb_emotion"])      # e.g. "hap"  (SpeechBrain label)
    print(result["confidence_score"])  # 0–100 fused score
"""

import logging
import os
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# SpeechBrain model cache (loaded once per process)
# ---------------------------------------------------------------------------
_SB_CLASSIFIER = None
_SB_AVAILABLE: Optional[bool] = None   # None = not yet checked

# HuggingFace model ID
_SB_MODEL_ID = "speechbrain/emotion-recognition-wav2vec2-IEMOCAP"

# Map SpeechBrain 4-class labels → human-readable interview emotion labels
_SB_LABEL_MAP: Dict[str, str] = {
    "ang": "anxious",
    "hap": "confident",
    "neu": "neutral",
    "sad": "uncertain",
}

# Weight SpeechBrain label → confidence score contribution (0–100 base)
_SB_CONFIDENCE_BASE: Dict[str, float] = {
    "hap": 75.0,   # happy → high confidence
    "neu": 55.0,   # neutral → moderate
    "sad": 35.0,   # sad → low confidence
    "ang": 40.0,   # angry → low-medium (nervousness)
}


def _get_sb_classifier():
    """Lazily load SpeechBrain classifier; returns None if unavailable."""
    global _SB_CLASSIFIER, _SB_AVAILABLE
    if _SB_AVAILABLE is False:
        return None
    if _SB_CLASSIFIER is not None:
        return _SB_CLASSIFIER
    try:
        from speechbrain.pretrained import EncoderClassifier
        logger.info("Loading SpeechBrain model: %s", _SB_MODEL_ID)
        _SB_CLASSIFIER = EncoderClassifier.from_hparams(
            source=_SB_MODEL_ID,
            savedir=os.path.join(os.path.expanduser("~"), ".cache", "speechbrain", "emotion"),
            run_opts={"device": "cpu"},
        )
        _SB_AVAILABLE = True
        logger.info("SpeechBrain emotion model loaded successfully")
        return _SB_CLASSIFIER
    except Exception as exc:
        logger.warning(
            "SpeechBrain not available (%s). Falling back to librosa heuristics.", exc
        )
        _SB_AVAILABLE = False
        return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def analyze_voice_emotion(audio_path: str) -> Dict[str, Any]:
    """Analyze emotional features from voice audio.

    Tries SpeechBrain wav2vec2 model first; falls back to librosa heuristics
    if SpeechBrain is unavailable or inference fails.

    Args:
        audio_path: Path to audio file (WAV/MP3/FLAC).

    Returns:
        Dict with voice emotion features.  All original keys are preserved.
        New keys: ``sb_emotion``, ``sb_scores``, ``sb_confidence``,
        ``analysis_mode`` (``'speechbrain'`` | ``'librosa'``).
    """
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    # Always run librosa for acoustic features (pitch, pauses, speaking rate)
    acoustic = _analyze_acoustic_features(audio_path)

    # Attempt SpeechBrain inference on top
    sb_result = _run_speechbrain(audio_path)

    if sb_result is not None:
        return _merge_results(acoustic, sb_result)

    # Pure librosa fallback
    acoustic["sb_emotion"] = None
    acoustic["sb_scores"] = {}
    acoustic["sb_confidence"] = None
    acoustic["analysis_mode"] = "librosa"
    return acoustic


# ---------------------------------------------------------------------------
# SpeechBrain inference
# ---------------------------------------------------------------------------

def _run_speechbrain(audio_path: str) -> Optional[Dict[str, Any]]:
    """Run SpeechBrain classifier; return dict or None on failure."""
    clf = _get_sb_classifier()
    if clf is None:
        return None
    try:
        import torchaudio
        signal, sr = torchaudio.load(audio_path)
        # SpeechBrain expects 16 kHz
        if sr != 16000:
            import torchaudio.transforms as T
            signal = T.Resample(orig_freq=sr, new_freq=16000)(signal)
        # Classify
        out_prob, score, index, text_lab = clf.classify_batch(signal)
        label = str(text_lab[0]).strip().lower()   # e.g. "hap"
        # Build per-class score dict
        import torch
        probs = torch.softmax(out_prob[0], dim=-1).tolist()
        labels = ["ang", "hap", "neu", "sad"]      # IEMOCAP order
        sb_scores = {l: round(p, 4) for l, p in zip(labels, probs)}
        return {
            "sb_emotion": label,
            "sb_scores": sb_scores,
            "sb_confidence": round(float(score[0]), 4),
        }
    except Exception as exc:
        logger.error("SpeechBrain inference failed: %s", exc)
        return None


def _merge_results(
    acoustic: Dict[str, Any],
    sb: Dict[str, Any],
) -> Dict[str, Any]:
    """Merge acoustic (librosa) features with SpeechBrain predictions.

    Fusion strategy:
      - SpeechBrain label wins for ``emotion_label`` (60 % weight)
      - Librosa confidence score is blended in (40 % weight)
      - Final ``confidence_score`` is a weighted blend
    """
    sb_label = sb["sb_emotion"]                        # e.g. "hap"
    human_label = _SB_LABEL_MAP.get(sb_label, "neutral")

    sb_base = _SB_CONFIDENCE_BASE.get(sb_label, 50.0)
    # Scale sb_base by how certain the model is (sb_confidence ~0–1)
    sb_conf_score = sb_base * min(1.0, sb["sb_confidence"] * 2)
    # Blend: 60 % SpeechBrain, 40 % librosa heuristic
    blended = 0.60 * sb_conf_score + 0.40 * acoustic["confidence_score"]

    result = {**acoustic}
    result["emotion_label"] = human_label
    result["confidence_score"] = round(min(100.0, max(0.0, blended)), 1)
    result["sb_emotion"] = sb_label
    result["sb_scores"] = sb["sb_scores"]
    result["sb_confidence"] = sb["sb_confidence"]
    result["analysis_mode"] = "speechbrain"
    return result


# ---------------------------------------------------------------------------
# Librosa acoustic analysis (unchanged logic from original, extracted)
# ---------------------------------------------------------------------------

def _analyze_acoustic_features(audio_path: str) -> Dict[str, Any]:
    """Extract acoustic features using librosa (original heuristic pipeline)."""
    try:
        import librosa
        import numpy as np
    except ImportError:
        logger.warning("librosa not available, returning defaults")
        return _default_voice_features()

    try:
        y, sr = librosa.load(audio_path, sr=None)
        if len(y) == 0:
            return _default_voice_features()

        # Pitch
        f0, voiced_flag, _ = librosa.pyin(
            y,
            fmin=librosa.note_to_hz("C2"),
            fmax=librosa.note_to_hz("C7"),
            sr=sr,
        )
        f0_clean = f0[~np.isnan(f0)] if f0 is not None else np.array([])
        pitch_mean = float(np.mean(f0_clean)) if len(f0_clean) > 0 else 0.0
        pitch_std  = float(np.std(f0_clean))  if len(f0_clean) > 0 else 0.0

        # Energy
        rms = librosa.feature.rms(y=y)[0]
        energy_mean = float(np.mean(rms))
        energy_std  = float(np.std(rms))

        # Spectral centroid
        spectral_mean = float(np.mean(librosa.feature.spectral_centroid(y=y, sr=sr)[0]))

        # ZCR
        zcr_mean = float(np.mean(librosa.feature.zero_crossing_rate(y)[0]))

        # Pauses
        rms_norm = rms / (np.max(rms) + 1e-8)
        is_silent = rms_norm < 0.05
        pause_ratio = float(np.mean(is_silent))

        diff = np.diff(is_silent.astype(int))
        pause_starts = np.where(diff == 1)[0]
        pause_ends   = np.where(diff == -1)[0]
        frame_dur = len(y) / sr / len(rms)
        short_pauses = sum(
            1 for s, e in zip(pause_starts, pause_ends)
            if 0.1 < (e - s) * frame_dur < 0.5
        )
        hesitation_detected = short_pauses >= 3

        # Speaking rate
        voiced_ratio = float(np.mean(voiced_flag)) if voiced_flag is not None else 0.5
        estimated_wpm = max(60, min(200, 80 + voiced_ratio * 100))

        # Heuristic confidence
        confidence_score = _calculate_voice_confidence(
            pitch_mean=pitch_mean,
            pitch_std=pitch_std,
            energy_mean=energy_mean,
            energy_std=energy_std,
            pause_ratio=pause_ratio,
            hesitation_detected=hesitation_detected,
            zcr_mean=zcr_mean,
        )

        emotion_label = _infer_emotion(pitch_mean, pitch_std, energy_mean, pause_ratio)

        return {
            "pitch_mean":         round(pitch_mean, 2),
            "pitch_std":          round(pitch_std, 2),
            "energy_mean":        round(energy_mean, 6),
            "energy_std":         round(energy_std, 6),
            "spectral_centroid":  round(spectral_mean, 2),
            "zcr_mean":           round(zcr_mean, 6),
            "speaking_speed":     round(estimated_wpm, 1),
            "pause_ratio":        round(pause_ratio, 3),
            "hesitation_detected": hesitation_detected,
            "short_pauses":       short_pauses,
            "emotion_label":      emotion_label,
            "confidence_score":   round(confidence_score, 1),
            "duration":           round(len(y) / sr, 2),
        }

    except Exception as exc:
        logger.error("Librosa acoustic analysis failed: %s", exc)
        return _default_voice_features(error=str(exc))


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
        "pitch_mean":           0.0,
        "pitch_std":            0.0,
        "energy_mean":          0.0,
        "energy_std":           0.0,
        "spectral_centroid":    0.0,
        "zcr_mean":             0.0,
        "speaking_speed":       120.0,
        "pause_ratio":          0.0,
        "hesitation_detected":  False,
        "short_pauses":         0,
        "emotion_label":        "neutral",
        "confidence_score":     50.0,
        "duration":             0.0,
        "sb_emotion":           None,
        "sb_scores":            {},
        "sb_confidence":        None,
        "analysis_mode":        "default",
        "error":                error,
    }
