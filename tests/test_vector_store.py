"""Tests for vector store abstraction and retrieval behaviour."""

from modules.rag.vector_stores.vector_store import SearchResult


def test_search_result_defaults():
    result = SearchResult(text="Python and FastAPI", score=0.91)
    assert result.text == "Python and FastAPI"
    assert result.score == 0.91
    assert result.metadata == {}
    assert result.doc_id is None
