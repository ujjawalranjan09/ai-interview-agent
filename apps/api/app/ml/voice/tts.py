"""Text-to-speech using gTTS and pyttsx3."""

import io
import logging

logger = logging.getLogger(__name__)

MAX_TEXT_LENGTH = 5000


def text_to_speech(text: str, language: str = "en", engine: str = "gtts") -> bytes:
    if not text.strip():
        raise ValueError("Text cannot be empty")
    if len(text) > MAX_TEXT_LENGTH:
        raise ValueError(f"Text exceeds max length of {MAX_TEXT_LENGTH} characters")

    if engine == "gtts":
        return _gtts_speak(text, language)
    elif engine == "pyttsx3":
        return _pyttsx3_speak(text)
    else:
        raise ValueError(f"Unknown TTS engine: {engine}")


def _gtts_speak(text: str, language: str) -> bytes:
    try:
        from gtts import gTTS
    except ImportError:
        raise ImportError("gTTS not installed")

    tts = gTTS(text=text, lang=language)
    buf = io.BytesIO()
    tts.write_to_fp(buf)
    return buf.getvalue()


def _pyttsx3_speak(text: str) -> bytes:
    try:
        import pyttsx3
        import tempfile
        import os
    except ImportError:
        raise ImportError("pyttsx3 not installed")

    engine = pyttsx3.init()
    engine.setProperty("rate", 150)
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    tmp.close()
    try:
        engine.save_to_file(text, tmp.name)
        engine.runAndWait()
        with open(tmp.name, "rb") as f:
            return f.read()
    finally:
        try:
            os.unlink(tmp.name)
        except OSError:
            pass
