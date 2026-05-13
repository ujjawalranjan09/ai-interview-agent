"""Abstract vector store interface for RAG backends."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class SearchResult:
    """Normalised retrieval result across vector store backends."""

    text: str
    score: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    doc_id: Optional[str] = None


class BaseVectorStore(ABC):
    """Backend-agnostic interface for persistent semantic retrieval."""

    @abstractmethod
    def upsert_documents(
        self,
        texts: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None,
    ) -> int:
        raise NotImplementedError

    @abstractmethod
    def similarity_search(
        self,
        query: str,
        top_k: int = 3,
        min_similarity: float = 0.15,
    ) -> List[SearchResult]:
        raise NotImplementedError

    @abstractmethod
    def count(self) -> int:
        raise NotImplementedError

    @abstractmethod
    def clear(self) -> None:
        raise NotImplementedError
