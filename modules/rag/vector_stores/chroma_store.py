"""Persistent ChromaDB vector store backend for RAG retrieval."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from .vector_store import BaseVectorStore, SearchResult

logger = logging.getLogger(__name__)

_model = None


def _get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        from app.config import SENTENCE_TRANSFORMER_MODEL

        _model = SentenceTransformer(SENTENCE_TRANSFORMER_MODEL)
        logger.info("Loaded Chroma embedding model: %s", SENTENCE_TRANSFORMER_MODEL)
    return _model


class ChromaVectorStore(BaseVectorStore):
    """ChromaDB-backed persistent store using local disk persistence."""

    def __init__(
        self,
        persist_directory: str = ".chroma",
        collection_name: str = "job_requirements",
    ):
        try:
            import chromadb
        except ImportError as exc:
            raise ImportError(
                "chromadb is required for ChromaVectorStore. Install with: pip install chromadb"
            ) from exc

        self._client = chromadb.PersistentClient(path=persist_directory)
        self._collection = self._client.get_or_create_collection(name=collection_name)
        self.collection_name = collection_name
        self.persist_directory = persist_directory

    def upsert_documents(
        self,
        texts: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None,
    ) -> int:
        if not texts:
            return 0

        model = _get_model()
        embeddings = model.encode(texts, show_progress_bar=False, normalize_embeddings=True)
        if ids is None:
            ids = [f"doc_{i}" for i in range(self.count(), self.count() + len(texts))]
        if metadatas is None:
            metadatas = [{} for _ in texts]

        self._collection.upsert(
            ids=ids,
            documents=texts,
            metadatas=metadatas,
            embeddings=[emb.tolist() for emb in embeddings],
        )
        return len(texts)

    def similarity_search(
        self,
        query: str,
        top_k: int = 3,
        min_similarity: float = 0.15,
    ) -> List[SearchResult]:
        if self.count() == 0:
            return []

        model = _get_model()
        query_embedding = model.encode([query], normalize_embeddings=True)[0].tolist()
        results = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )

        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]
        ids = results.get("ids", [[]])[0] if results.get("ids") else [None] * len(documents)

        output: List[SearchResult] = []
        for doc, meta, distance, doc_id in zip(documents, metadatas, distances, ids):
            score = 1.0 - float(distance)
            if score >= min_similarity:
                output.append(SearchResult(text=doc, score=score, metadata=meta or {}, doc_id=doc_id))
        return output

    def count(self) -> int:
        return self._collection.count()

    def clear(self) -> None:
        self._client.delete_collection(self.collection_name)
        self._collection = self._client.get_or_create_collection(name=self.collection_name)
