"""Speech emotion recognition using SpeechBrain wav2vec2-IEMOCAP from HuggingFace.

Model: speechbrain/emotion-recognition-wav2vec2-IEMOCAP
Downloads: 613K+ | License: Apache 2.0
Link: https://hf.co/speechbrain/emotion-recognition-wav2vec2-IEMOCAP

This module provides deep-learning-based speech emotion recognition
directly from audio waveforms, replacing the previous rule-based
heuristic approach. It detects: angry, happy, neutral, sad, fearful.
"""

import logging
import os
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Lazy-loaded model to avoid heavy startup cost
_classifier = None
_model_source = "speechbrain/emotion-recognition-wav2vec2-IEMOCAP"

# Emotion label mapping from IEMOCAP dataset labels to human-readable
_EMOTION_MAP = {
    "ang": "angry",
    "hap": "happy",
    "neu": "neutral",
    "sad": "sad",
    "fru": "frustrated",
    "exc": "excited",
    "fea": "fearful",
    "dis": "disgusted",
    "sur": "surprised",
    "oth": "other",
}

# Confidence impact: how each emotion affects interview confidence score
_EMOTION_CONFIDENCE_IMPACT = {
    "happy": +15,
    "excited": +12,
    "neutral": +5,
    "confident": +10,
    "calm": +8,
    "sad": -10,
    "angry": -8,
    "fearful": -20,
    "frustrated": -15,
    "disgusted": -12,
    "surprised": 0,
    "other": 0,
}


def _get_classifier():
    """Lazily load the SpeechBrain emotion classifier."""
    global _classifier
    if _classifier is None:
        try:
            from speechbrain.inference.interfaces import foreign_class
            import tempfile

            savedir = os.path.join(
                tempfile.gettempdir(), "speechbrain_emotion_cache"
            )
            logger.info(
                f"Loading SpeechBrain emotion model from HuggingFace: {_model_source}"
            )
            _classifier = foreign_class(
                source=_model_source,
                pymodule_file="custom_interface.py",
                classname="CustomEncoderWav2vec2Classifier",
                savedir=savedir,
            )
            logger.info("SpeechBrain emotion model loaded successfully.")
        except ImportError:
            raise ImportError(
                "speechbrain not installed. Run: pip install speechbrain"
            )
        except Exception as e:
            logger.error(f"Failed to load SpeechBrain model: {e}")
            raise
    return _classifier


def classify_emotion(audio_path: str) -> Dict[str, Any]:
    """Classify emotion from an audio file using SpeechBrain wav2vec2.

    Args:
        audio_path: Path to a WAV audio file (16kHz mono recommended).

    Returns:
        Dictionary with:
            - emotion: Predicted emotion string (e.g. 'happy', 'neutral')
            - emotion_raw: Raw model label (e.g. 'hap')
            - score: Model confidence score (0.0 - 1.0)
            - all_scores: Dict of all emotion probabilities
            - confidence_impact: Interview confidence delta from this emotion
            - model: Model identifier used
    """
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    try:
        classifier = _get_classifier()

        # SpeechBrain classify_file returns (out_prob, score, index, text_lab)
        out_prob, score, index, text_lab = classifier.classify_file(audio_path)

        raw_label = text_lab[0] if isinstance(text_lab, list) else str(text_lab)
        emotion = _EMOTION_MAP.get(raw_label, raw_label)
        confidence_score = float(score.item()) if hasattr(score, "item") else float(score)

        # Build full probability dict if available
        all_scores = {}
        if out_prob is not None:
            try:
                import torch
                probs = torch.softmax(out_prob, dim=-1).squeeze()
                labels = classifier.hparams.label_encoder.decode_ndim(
                    list(range(len(probs)))
                )
                all_scores = {
                    _EMOTION_MAP.get(l, l): round(float(p), 4)
                    for l, p in zip(labels, probs.tolist())
                }
            except Exception:
                pass  # all_scores stays empty — non-critical

        impact = _EMOTION_CONFIDENCE_IMPACT.get(emotion, 0)

        logger.info(
            f"SpeechBrain emotion: {emotion} (raw={raw_label}, score={confidence_score:.3f})"
        )

        return {
            "emotion": emotion,
            "emotion_raw": raw_label,
            "score": round(confidence_score, 4),
            "all_scores": all_scores,
            "confidence_impact": impact,
            "model": _model_source,
        }

    except ImportError as e:
        logger.warning(f"SpeechBrain not available, using fallback: {e}")
        return _fallback_result(str(e))
    except Exception as e:
        logger.error(f"SpeechBrain emotion classification failed: {e}")
        return _fallback_result(str(e))


def classify_emotion_batch(audio_paths: list) -> list:
    """Classify emotions for multiple audio files.

    Args:
        audio_paths: List of paths to audio files.

    Returns:
        List of classification result dicts.
    """
    return [classify_emotion(p) for p in audio_paths]


def is_model_available() -> bool:
    """Check if the SpeechBrain model can be loaded."""
    try:
        _get_classifier()
        return True
    except Exception:
        return False


def _fallback_result(error: str = "") -> Dict[str, Any]:
    """Return a neutral fallback when the model is unavailable."""
    return {
        "emotion": "neutral",
        "emotion_raw": "neu",
        "score": 0.5,
        "all_scores": {},
        "confidence_impact": 0,
        "model": "fallback",
        "error": error,
    }
