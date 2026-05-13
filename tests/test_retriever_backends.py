"""Integration tests for the multi-backend Retriever."""

from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from modules.rag.retriever import Retriever, DocumentChunk


# ── helpers ──────────────────────────────────────────────────────────────────

def _make_fake_model(dim: int = 8):
    """Return a fake SentenceTransformer that emits unit vectors."""
    m = MagicMock()
    def encode(texts, show_progress_bar=False, normalize_embeddings=False):
        n = len(texts) if isinstance(texts, list) else 1
        vecs = np.random.rand(n, dim).astype("float32")
        norms = np.linalg.norm(vecs, axis=1, keepdims=True)
        return vecs / norms
    m.encode.side_effect = encode
    return m


# ── memory backend ────────────────────────────────────────────────────────────

def test_memory_backend_load_and_retrieve():
    with patch("modules.rag.retriever._get_model", return_value=_make_fake_model()):
        r = Retriever(backend="memory")
        n = r.load_document("Python FastAPI microservices", source="jd")
        assert n >= 1
        assert r.is_ready
        results = r.retrieve("Python", top_k=3)
        assert len(results) >= 0


def test_memory_backend_clear():
    with patch("modules.rag.retriever._get_model", return_value=_make_fake_model()):
        r = Retriever(backend="memory")
        r.load_document("Some job description text about Python.")
        r.clear()
        assert not r.is_ready
        assert r.chunk_count == 0


# ── chroma backend ─────────────────────────────────────────────────────────────

def test_chroma_backend_delegates_to_store(tmp_path):
    from modules.rag.vector_stores.vector_store import SearchResult

    fake_store = MagicMock()
    fake_store.count.return_value = 1
    fake_store.similarity_search.return_value = [
        SearchResult(text="Use FastAPI for REST APIs", score=0.88, metadata={"source": "jd"})
    ]

    with patch("modules.rag.retriever.Retriever._get_store", return_value=fake_store):
        r = Retriever(backend="chroma", persist_directory=str(tmp_path))
        r._vector_store = fake_store
        r.load_document("FastAPI REST microservices")
        assert r.chunk_count == 1
        results = r.retrieve("FastAPI", top_k=3)
        assert len(results) >= 1
        chunk, score = results[0]
        assert isinstance(chunk, DocumentChunk)
        assert score == pytest.approx(0.88)


# ── faiss backend ──────────────────────────────────────────────────────────────

def test_faiss_backend_delegates_to_store():
    from modules.rag.vector_stores.vector_store import SearchResult

    fake_store = MagicMock()
    fake_store.count.return_value = 2
    fake_store.similarity_search.return_value = [
        SearchResult(text="TensorFlow ML pipelines", score=0.75, metadata={})
    ]

    with patch("modules.rag.retriever.Retriever._get_store", return_value=fake_store):
        r = Retriever(backend="faiss")
        r._vector_store = fake_store
        r.load_document("TensorFlow machine learning pipelines")
        results = r.retrieve("TensorFlow", top_k=3)
        assert len(results) >= 1


# ── backend validation ────────────────────────────────────────────────────────

def test_invalid_backend_raises():
    with pytest.raises(ValueError, match="backend must be one of"):
        Retriever(backend="redis")
