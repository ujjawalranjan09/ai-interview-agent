"""Tests for the upgraded voice emotion module and multimodal fusion layer."""

import os
import tempfile
from unittest.mock import MagicMock, patch

import numpy as np
import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_silent_wav(path: str, duration: float = 1.0, sr: int = 16000) -> None:
    """Write a minimal silent WAV file for testing."""
    import wave, struct
    n_samples = int(sr * duration)
    with wave.open(path, "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(struct.pack("<" + "h" * n_samples, *([0] * n_samples)))


# ---------------------------------------------------------------------------
# voice_emotion — librosa fallback path
# ---------------------------------------------------------------------------

class TestLibrosaFallback:
    """When SpeechBrain is not installed, fall back to librosa gracefully."""

    def test_returns_all_expected_keys(self, tmp_path):
        wav = str(tmp_path / "test.wav")
        _write_silent_wav(wav)

        with patch("modules.voice.voice_emotion._get_sb_classifier", return_value=None):
            from modules.voice.voice_emotion import analyze_voice_emotion
            result = analyze_voice_emotion(wav)

        expected_keys = [
            "pitch_mean", "pitch_std", "energy_mean", "energy_std",
            "spectral_centroid", "zcr_mean", "speaking_speed",
            "pause_ratio", "hesitation_detected", "short_pauses",
            "emotion_label", "confidence_score", "duration",
            "sb_emotion", "sb_scores", "sb_confidence", "analysis_mode",
        ]
        for key in expected_keys:
            assert key in result, f"Missing key: {key}"

    def test_analysis_mode_is_librosa(self, tmp_path):
        wav = str(tmp_path / "test.wav")
        _write_silent_wav(wav)

        with patch("modules.voice.voice_emotion._get_sb_classifier", return_value=None):
            from modules.voice.voice_emotion import analyze_voice_emotion
            result = analyze_voice_emotion(wav)

        assert result["analysis_mode"] == "librosa"
        assert result["sb_emotion"] is None

    def test_raises_on_missing_file(self):
        from modules.voice.voice_emotion import analyze_voice_emotion
        with pytest.raises(FileNotFoundError):
            analyze_voice_emotion("/nonexistent/path/file.wav")


# ---------------------------------------------------------------------------
# voice_emotion — SpeechBrain mock path
# ---------------------------------------------------------------------------

class TestSpeechBrainPath:
    """Mock SpeechBrain inference and verify fusion logic."""

    def _make_mock_classifier(self, label: str = "hap", score: float = 0.85):
        import torch
        clf = MagicMock()
        # probs: [ang, hap, neu, sad]
        idx = ["ang", "hap", "neu", "sad"].index(label)
        prob_tensor = torch.zeros(1, 4)
        prob_tensor[0, idx] = score
        # Normalise
        prob_tensor = prob_tensor / prob_tensor.sum()
        score_tensor = torch.tensor([score])
        clf.classify_batch.return_value = (prob_tensor.unsqueeze(0), score_tensor, torch.tensor([idx]), [label])
        return clf

    def test_speechbrain_happy_path(self, tmp_path):
        wav = str(tmp_path / "happy.wav")
        _write_silent_wav(wav)

        mock_clf = self._make_mock_classifier(label="hap", score=0.9)

        with patch("modules.voice.voice_emotion._get_sb_classifier", return_value=mock_clf), \
             patch("torchaudio.load") as mock_load:
            import torch
            mock_load.return_value = (torch.zeros(1, 16000), 16000)
            from modules.voice.voice_emotion import analyze_voice_emotion
            result = analyze_voice_emotion(wav)

        assert result["analysis_mode"] == "speechbrain"
        assert result["sb_emotion"] == "hap"
        assert result["emotion_label"] == "confident"
        assert 0 <= result["confidence_score"] <= 100

    def test_speechbrain_nervous_maps_correctly(self, tmp_path):
        wav = str(tmp_path / "nervous.wav")
        _write_silent_wav(wav)

        mock_clf = self._make_mock_classifier(label="sad", score=0.8)

        with patch("modules.voice.voice_emotion._get_sb_classifier", return_value=mock_clf), \
             patch("torchaudio.load") as mock_load:
            import torch
            mock_load.return_value = (torch.zeros(1, 16000), 16000)
            from modules.voice.voice_emotion import analyze_voice_emotion
            result = analyze_voice_emotion(wav)

        assert result["emotion_label"] == "uncertain"


# ---------------------------------------------------------------------------
# Multimodal fusion
# ---------------------------------------------------------------------------

class TestEmotionFusion:
    def _audio_result(self, emotion="confident", score=75.0):
        return {
            "confidence_score": score,
            "emotion_label": emotion,
            "analysis_mode": "speechbrain",
            "sb_emotion": "hap",
            "sb_scores": {"ang": 0.05, "hap": 0.80, "neu": 0.10, "sad": 0.05},
            "sb_confidence": 0.85,
            "hesitation_detected": False,
            "pause_ratio": 0.15,
            "speaking_speed": 130.0,
            "pitch_std": 45.0,
        }

    def _face_result(self, emotion="neutral", score=55.0):
        return {
            "confidence_score": score,
            "dominant_emotion": emotion,
        }

    def test_fuse_both_modalities(self):
        from modules.video.emotion_fusion import fuse_emotions, FusedEmotionResult
        result = fuse_emotions(
            audio_result=self._audio_result(),
            face_result=self._face_result(),
        )
        assert isinstance(result, FusedEmotionResult)
        assert 0 <= result.confidence_score <= 100
        assert result.emotion_label in {
            "confident", "neutral", "calm", "uncertain",
            "nervous", "anxious", "excited", "happy",
        }

    def test_fuse_audio_only(self):
        from modules.video.emotion_fusion import fuse_emotions
        result = fuse_emotions(audio_result=self._audio_result(), face_result=None)
        assert result.confidence_score == pytest.approx(75.0, abs=1.0)
        assert result.analysis_mode == "speechbrain"

    def test_verdict_levels(self):
        from modules.video.emotion_fusion import get_interview_verdict
        assert get_interview_verdict(80) == "Highly Confident"
        assert get_interview_verdict(62) == "Confident"
        assert get_interview_verdict(50) == "Moderate"
        assert get_interview_verdict(35) == "Nervous"
        assert get_interview_verdict(10) == "Highly Nervous"

    def test_to_dict_has_all_keys(self):
        from modules.video.emotion_fusion import fuse_emotions
        result = fuse_emotions(
            audio_result=self._audio_result(),
            face_result=self._face_result(),
        )
        d = result.to_dict()
        required = [
            "confidence_score", "emotion_label", "verdict",
            "audio_confidence", "face_confidence",
            "audio_emotion", "face_emotion",
            "sb_emotion", "sb_scores", "analysis_mode",
            "hesitation_detected", "pause_ratio", "speaking_speed",
        ]
        for k in required:
            assert k in d, f"Missing key in to_dict(): {k}"
