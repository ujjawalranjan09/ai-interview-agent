"""Vector store backends for persistent RAG retrieval.

Adds ChromaDB and FAISS support while preserving the existing Retriever API.
Chroma is the recommended default because it persists embeddings and metadata
across restarts without extra serialization code.
"""

from .vector_store import BaseVectorStore, SearchResult
from .chroma_store import ChromaVectorStore
from .faiss_store import FaissVectorStore

__all__ = [
    "BaseVectorStore",
    "SearchResult",
    "ChromaVectorStore",
    "FaissVectorStore",
]
