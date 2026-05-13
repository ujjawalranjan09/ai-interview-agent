"""Unit tests for modules/rag/session_store.py.

ChromaDB is mocked — no model download or disk write needed in CI.
"""

from unittest.mock import MagicMock, patch

import pytest

from modules.rag.session_store import SessionStore

SESSION_ID = "test-session-001"
CANDIDATE_ID = "candidate-ujjawal"


@pytest.fixture()
def store():
    mock_collection = MagicMock()
    mock_collection.get.return_value = {
        "documents": ["Q: Python?\nA: It is a language."],
        "metadatas": [{"session_id": SESSION_ID, "question_index": 0, "confidence_score": 72.0,
                        "candidate_id": CANDIDATE_ID, "emotion_label": "confident"}],
    }
    mock_collection.query.return_value = {"documents": [["Q: Python?\nA: It is a language."]]}

    mock_client = MagicMock()
    mock_client.get_or_create_collection.return_value = mock_collection

    with (
        patch("modules.rag.session_store.chromadb", create=True) as mock_chroma,
        patch(
            "modules.rag.session_store.SentenceTransformerEmbeddingFunction",
            return_value=MagicMock(),
            create=True,
        ),
    ):
        mock_chroma.PersistentClient.return_value = mock_client
        ss = SessionStore.__new__(SessionStore)
        ss.session_id = SESSION_ID
        ss.candidate_id = CANDIDATE_ID
        ss.client = mock_client
        ss._embed_fn = MagicMock()
        ss._collection = mock_collection
        yield ss, mock_collection


def test_store_answer_calls_upsert(store):
    ss, coll = store
    doc_id = ss.store_answer(
        question="What is Python?",
        answer="A programming language.",
        question_index=0,
        confidence_score=72.0,
        emotion_label="confident",
    )
    coll.upsert.assert_called_once()
    assert doc_id == f"{SESSION_ID}-q0"


def test_get_session_history_returns_list(store):
    ss, _ = store
    history = ss.get_session_history()
    assert isinstance(history, list)
    assert len(history) > 0


def test_get_context_chunks_returns_strings(store):
    ss, _ = store
    chunks = ss.get_context_chunks("Python skills")
    assert isinstance(chunks, list)
    assert all(isinstance(c, str) for c in chunks)


def test_get_confidence_timeline_returns_floats(store):
    ss, _ = store
    timeline = ss.get_confidence_timeline()
    assert isinstance(timeline, list)
    assert all(isinstance(v, float) for v in timeline)


def test_get_candidate_weak_areas(store):
    ss, coll = store
    coll.get.return_value = {
        "documents": ["Q: DSA?\nA: Not sure.", "Q: Python?\nA: Yes."],
        "metadatas": [
            {"confidence_score": 30.0, "candidate_id": CANDIDATE_ID},
            {"confidence_score": 85.0, "candidate_id": CANDIDATE_ID},
        ],
    }
    weak = ss.get_candidate_weak_areas(confidence_threshold=45.0)
    assert len(weak) == 1
    assert weak[0]["metadata"]["confidence_score"] == 30.0


def test_get_candidate_session_ids(store):
    ss, coll = store
    coll.get.return_value = {
        "metadatas": [
            {"session_id": "s1", "candidate_id": CANDIDATE_ID},
            {"session_id": "s2", "candidate_id": CANDIDATE_ID},
            {"session_id": "s1", "candidate_id": CANDIDATE_ID},
        ],
    }
    ids = ss.get_candidate_session_ids()
    assert len(ids) == 2
    assert "s1" in ids
    assert "s2" in ids
