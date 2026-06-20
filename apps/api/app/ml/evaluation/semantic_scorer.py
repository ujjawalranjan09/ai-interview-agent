"""Semantic similarity scoring using sentence-transformers."""

import logging

logger = logging.getLogger(__name__)

_model = None


def _get_model():
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
            from app.core.config import settings
            _model = SentenceTransformer(settings.SENTENCE_TRANSFORMER_MODEL)
        except ImportError:
            logger.warning("sentence-transformers not available, using fallback")
            _model = False
    return _model if _model else None


def compute_similarity(text1: str, text2: str) -> float:
    if not text1.strip() or not text2.strip():
        return 0.0

    model = _get_model()
    if model:
        try:
            embeddings = model.encode([text1, text2])
            from numpy import dot
            from numpy.linalg import norm
            sim = dot(embeddings[0], embeddings[1]) / (norm(embeddings[0]) * norm(embeddings[1]))
            return float(max(0.0, min(1.0, sim)))
        except Exception as e:
            logger.warning("Sentence transformer similarity failed: %s", e)

    return _fallback_similarity(text1, text2)


def _fallback_similarity(text1: str, text2: str) -> float:
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())
    if not words1 or not words2:
        return 0.0
    return len(words1 & words2) / len(words1 | words2)
