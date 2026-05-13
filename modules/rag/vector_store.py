"""Persistent Chroma vector store for the interview RAG pipeline.

Uses HuggingFace sentence-transformers/all-MiniLM-L6-v2 as the default
embedding function, consistent with the existing sentence-transformers
dependency in requirements.txt.

Chroma docs: https://docs.trychroma.com/integrations/embedding-models/hugging-face
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

DEFAULT_EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
COLLECTIONS = [
    "candidate_resume",
    "job_description",
    "question_bank",
    "interview_memory",
]


class InterviewVectorStore:
    """Wrapper around a persistent Chroma client for interview materials."""

    def __init__(
        self,
        persist_path: str = "database/chroma",
        embed_model: str = DEFAULT_EMBED_MODEL,
    ) -> None:
        import chromadb  # noqa: PLC0415
        from chromadb.utils.embedding_functions import (
            SentenceTransformerEmbeddingFunction,  # noqa: PLC0415
        )

        logger.info("Initialising Chroma persistent store at: %s", persist_path)
        self.client = chromadb.PersistentClient(path=persist_path)
        self.embedding_fn = SentenceTransformerEmbeddingFunction(
            model_name=embed_model
        )

    # ------------------------------------------------------------------
    # Collection helpers
    # ------------------------------------------------------------------

    def get_collection(self, name: str):
        """Get or create a named collection with the default embedding fn."""
        if name not in COLLECTIONS:
            raise ValueError(
                f"Unknown collection '{name}'. Valid: {COLLECTIONS}"
            )
        return self.client.get_or_create_collection(
            name=name,
            embedding_function=self.embedding_fn,
        )

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def add_documents(
        self,
        collection_name: str,
        docs: List[Dict[str, Any]],
    ) -> None:
        """Upsert documents into a collection.

        Each doc dict must have:
          - ``id``       (str, unique)
          - ``text``     (str)
          - ``metadata`` (dict, optional)
        """
        if not docs:
            return
        collection = self.get_collection(collection_name)
        collection.upsert(
            ids=[d["id"] for d in docs],
            documents=[d["text"] for d in docs],
            metadatas=[d.get("metadata", {}) for d in docs],
        )
        logger.info(
            "Upserted %d documents into collection '%s'",
            len(docs),
            collection_name,
        )

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def query(
        self,
        collection_name: str,
        query_text: str,
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None,
    ) -> dict:
        """Semantic similarity search.

        Returns the raw Chroma query result dict.
        """
        collection = self.get_collection(collection_name)
        kwargs: dict[str, Any] = {
            "query_texts": [query_text],
            "n_results": n_results,
        }
        if where:
            kwargs["where"] = where
        return collection.query(**kwargs)

    def get_top_chunks(
        self,
        collection_name: str,
        query_text: str,
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None,
    ) -> List[str]:
        """Convenience method — returns just the document strings."""
        result = self.query(collection_name, query_text, n_results, where)
        docs = result.get("documents", [[]])[0]
        return docs

    def clear_collection(self, collection_name: str) -> None:
        """Delete all items in a collection (non-destructive to the collection itself)."""
        collection = self.get_collection(collection_name)
        all_ids = collection.get()["ids"]
        if all_ids:
            collection.delete(ids=all_ids)
            logger.info("Cleared %d items from '%s'", len(all_ids), collection_name)


# ------------------------------------------------------------------
# Utility
# ------------------------------------------------------------------

def chunk_text(
    text: str,
    chunk_size: int = 500,
    overlap: int = 80,
) -> List[str]:
    """Split text into overlapping chunks for embedding."""
    text = " ".join(text.split())  # normalise whitespace
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(len(text), start + chunk_size)
        chunks.append(text[start:end])
        if end == len(text):
            break
        start = max(0, end - overlap)
    return chunks
