"""FAISS vector store backend for fast local semantic retrieval."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import numpy as np

from .vector_store import BaseVectorStore, SearchResult

logger = logging.getLogger(__name__)

_model = None


def _get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        from app.config import SENTENCE_TRANSFORMER_MODEL

        _model = SentenceTransformer(SENTENCE_TRANSFORMER_MODEL)
        logger.info("Loaded FAISS embedding model: %s", SENTENCE_TRANSFORMER_MODEL)
    return _model


class FaissVectorStore(BaseVectorStore):
    """Simple FAISS-backed store with in-process metadata mapping."""

    def __init__(self):
        try:
            import faiss
        except ImportError as exc:
            raise ImportError(
                "faiss-cpu is required for FaissVectorStore. Install with: pip install faiss-cpu"
            ) from exc

        self.faiss = faiss
        self._index = None
        self._texts: List[str] = []
        self._metadatas: List[Dict[str, Any]] = []
        self._ids: List[str] = []

    def upsert_documents(
        self,
        texts: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None,
    ) -> int:
        if not texts:
            return 0

        model = _get_model()
        embeddings = np.array(model.encode(texts, show_progress_bar=False, normalize_embeddings=True)).astype("float32")

        if self._index is None:
            dim = embeddings.shape[1]
            self._index = self.faiss.IndexFlatIP(dim)

        self._index.add(embeddings)
        base = len(self._texts)
        self._texts.extend(texts)
        self._metadatas.extend(metadatas or [{} for _ in texts])
        self._ids.extend(ids or [f"doc_{base + i}" for i in range(len(texts))])
        return len(texts)

    def similarity_search(
        self,
        query: str,
        top_k: int = 3,
        min_similarity: float = 0.15,
    ) -> List[SearchResult]:
        if self._index is None or not self._texts:
            return []

        model = _get_model()
        query_embedding = np.array(model.encode([query], normalize_embeddings=True)).astype("float32")
        scores, indices = self._index.search(query_embedding, top_k)

        output: List[SearchResult] = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0:
                continue
            similarity = float(score)
            if similarity >= min_similarity:
                output.append(
                    SearchResult(
                        text=self._texts[idx],
                        score=similarity,
                        metadata=self._metadatas[idx],
                        doc_id=self._ids[idx],
                    )
                )
        return output

    def count(self) -> int:
        return len(self._texts)

    def clear(self) -> None:
        self._index = None
        self._texts = []
        self._metadatas = []
        self._ids = []
