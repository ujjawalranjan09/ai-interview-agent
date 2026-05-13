"""Unit tests for modules/rag/vector_store.py.

ChromaDB and SentenceTransformer are mocked to avoid model downloads in CI.
"""

from unittest.mock import MagicMock, patch

import pytest

from modules.rag.vector_store import InterviewVectorStore, chunk_text


@pytest.fixture()
def store():
    """InterviewVectorStore with mocked Chroma internals."""
    mock_collection = MagicMock()
    mock_collection.query.return_value = {"documents": [["chunk1", "chunk2"]]}
    mock_collection.get.return_value = {"ids": []}

    mock_client = MagicMock()
    mock_client.get_or_create_collection.return_value = mock_collection

    mock_embed_fn = MagicMock()

    with (
        patch("modules.rag.vector_store.chromadb", create=True) as mock_chromadb,
        patch(
            "modules.rag.vector_store.SentenceTransformerEmbeddingFunction",
            return_value=mock_embed_fn,
            create=True,
        ),
    ):
        mock_chromadb.PersistentClient.return_value = mock_client
        vs = InterviewVectorStore.__new__(InterviewVectorStore)
        vs.client = mock_client
        vs.embedding_fn = mock_embed_fn
        yield vs, mock_collection


def test_add_documents(store):
    vs, coll = store
    docs = [
        {"id": "r-0", "text": "Python developer", "metadata": {"source_type": "candidate_resume"}},
    ]
    with patch.object(vs, "get_collection", return_value=coll):
        vs.add_documents("candidate_resume", docs)
    coll.upsert.assert_called_once()


def test_get_top_chunks_returns_list(store):
    vs, coll = store
    with patch.object(vs, "get_collection", return_value=coll):
        result = vs.get_top_chunks("candidate_resume", "Python skills")
    assert isinstance(result, list)
    assert "chunk1" in result


def test_add_empty_docs_is_noop(store):
    vs, coll = store
    with patch.object(vs, "get_collection", return_value=coll):
        vs.add_documents("candidate_resume", [])
    coll.upsert.assert_not_called()


@pytest.mark.parametrize(
    "text,chunk_size,expected_min_chunks",
    [
        ("a" * 1200, 500, 3),
        ("short text", 500, 1),
        ("", 500, 0),
    ],
)
def test_chunk_text(text, chunk_size, expected_min_chunks):
    result = chunk_text(text, chunk_size=chunk_size)
    assert len(result) >= expected_min_chunks
