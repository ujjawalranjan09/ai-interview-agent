"""Unit tests for the SpeechBrain emotion module (mocked — no model download in CI)."""

import pytest
from unittest.mock import patch, MagicMock
import os
import tempfile


class TestClassifyEmotion:
    def test_file_not_found_raises(self):
        from modules.voice.speechbrain_emotion import classify_emotion
        with pytest.raises(FileNotFoundError):
            classify_emotion("/nonexistent/path/audio.wav")

    def test_fallback_on_import_error(self):
        from modules.voice.speechbrain_emotion import _fallback_result
        result = _fallback_result("speechbrain not installed")
        assert result["emotion"] == "neutral"
        assert result["score"] == 0.5
        assert "error" in result

    @patch("modules.voice.speechbrain_emotion._get_classifier")
    def test_classify_returns_correct_keys(self, mock_get_clf):
        # Create a temporary WAV file for the path check
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            tmp_path = f.name

        try:
            # Mock the classifier output
            mock_clf = MagicMock()
            mock_clf.classify_file.return_value = (
                None,   # out_prob
                0.87,   # score
                2,      # index
                ["hap"],  # text_lab
            )
            mock_get_clf.return_value = mock_clf

            from modules.voice.speechbrain_emotion import classify_emotion
            result = classify_emotion(tmp_path)

            assert result["emotion"] == "happy"
            assert result["emotion_raw"] == "hap"
            assert result["score"] == pytest.approx(0.87, abs=0.01)
            assert result["confidence_impact"] == 15  # happy = +15
            assert result["model"] == "speechbrain/emotion-recognition-wav2vec2-IEMOCAP"
        finally:
            os.unlink(tmp_path)

    @patch("modules.voice.speechbrain_emotion._get_classifier")
    def test_nervous_emotion_negative_impact(self, mock_get_clf):
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            tmp_path = f.name
        try:
            mock_clf = MagicMock()
            mock_clf.classify_file.return_value = (None, 0.9, 0, ["fea"])
            mock_get_clf.return_value = mock_clf

            from modules.voice.speechbrain_emotion import classify_emotion
            result = classify_emotion(tmp_path)

            assert result["emotion"] == "fearful"
            assert result["confidence_impact"] < 0
        finally:
            os.unlink(tmp_path)

    def test_is_model_available_false_when_not_installed(self):
        with patch("modules.voice.speechbrain_emotion._get_classifier",
                   side_effect=ImportError("no speechbrain")):
            from modules.voice.speechbrain_emotion import is_model_available
            assert is_model_available() is False
