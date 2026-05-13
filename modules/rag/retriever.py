"""Document retriever for job descriptions — chunking, embedding, and similarity search.

Now supports three backends controlled by the `backend` parameter:
  - ``memory``  (default) — original in-process NumPy store (no persistence)
  - ``chroma``  — ChromaDB PersistentClient; survives restarts (recommended)
  - ``faiss``   — FAISS IndexFlatIP; fastest for large corpora

Existing callers that create ``Retriever()`` continue to work unchanged.
"""

import logging
import os
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)

# Lazy-loaded sentence transformer (cached at module level across all Retriever instances)
_model = None


def _get_model():
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
            from app.config import SENTENCE_TRANSFORMER_MODEL
            _model = SentenceTransformer(SENTENCE_TRANSFORMER_MODEL)
            logger.info("Loaded embedding model: %s", SENTENCE_TRANSFORMER_MODEL)
        except ImportError as exc:
            raise ImportError(
                "sentence-transformers is required. Install with: pip install sentence-transformers"
            ) from exc
    return _model


@dataclass
class DocumentChunk:
    """A chunk of a document with its embedding."""

    text: str
    chunk_id: int
    metadata: Dict[str, Any] = field(default_factory=dict)
    embedding: Optional[np.ndarray] = None

    def to_dict(self) -> Dict[str, Any]:
        return {"text": self.text, "chunk_id": self.chunk_id, "metadata": self.metadata}


class Retriever:
    """Retrieval engine for job description documents.

    Chunks documents, creates embeddings, and retrieves the most relevant
    chunks for a given query using cosine similarity.

    Args:
        chunk_size:         Maximum characters per chunk.
        chunk_overlap:      Overlap between consecutive chunks (characters).
        backend:            ``'memory'`` | ``'chroma'`` | ``'faiss'``.
                            Defaults to ``'memory'`` for backward compatibility.
        persist_directory:  Only used when backend is ``'chroma'``.
                            Directory where ChromaDB stores its data.
        collection_name:    ChromaDB collection name.
    """

    BACKENDS = ("memory", "chroma", "faiss")

    def __init__(
        self,
        chunk_size: int = 512,
        chunk_overlap: int = 64,
        backend: str = "memory",
        persist_directory: str = ".chroma",
        collection_name: str = "job_requirements",
    ):
        if backend not in self.BACKENDS:
            raise ValueError(f"backend must be one of {self.BACKENDS}, got '{backend}'")

        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.backend = backend

        # Memory backend state (unchanged)
        self._chunks: List[DocumentChunk] = []
        self._embeddings_matrix: Optional[np.ndarray] = None

        # Persistent backend (lazy-created on first use)
        self._vector_store = None
        self._persist_directory = persist_directory
        self._collection_name = collection_name

    # ── Backend initialisation ─────────────────────────────────────────────────

    def _get_store(self):
        """Lazily initialise and return the persistent vector store."""
        if self._vector_store is not None:
            return self._vector_store

        if self.backend == "chroma":
            from modules.rag.vector_stores.chroma_store import ChromaVectorStore
            self._vector_store = ChromaVectorStore(
                persist_directory=self._persist_directory,
                collection_name=self._collection_name,
            )
        elif self.backend == "faiss":
            from modules.rag.vector_stores.faiss_store import FaissVectorStore
            self._vector_store = FaissVectorStore()
        return self._vector_store

    # ── Properties ─────────────────────────────────────────────────────────────

    @property
    def chunk_count(self) -> int:
        if self.backend == "memory":
            return len(self._chunks)
        return self._get_store().count()

    @property
    def is_ready(self) -> bool:
        if self.backend == "memory":
            return self._embeddings_matrix is not None and len(self._chunks) > 0
        return self._get_store().count() > 0

    # ── Public API ─────────────────────────────────────────────────────────────

    def load_document(
        self,
        text: str,
        source: str = "job_description",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> int:
        """Load and index a document from raw text."""
        if not text or not text.strip():
            raise ValueError("Document text cannot be empty")

        base_metadata = {**(metadata or {}), "source": source}
        cleaned = self._clean_text(text)
        raw_chunks = self._split_into_chunks(cleaned)

        if not raw_chunks:
            logger.warning("No chunks produced for source '%s'", source)
            return 0

        if self.backend == "memory":
            model = _get_model()
            encoded = model.encode(raw_chunks, show_progress_bar=False, normalize_embeddings=True)
            chunks: List[DocumentChunk] = []
            embeddings_list: List[np.ndarray] = []
            for i, (chunk_text, emb) in enumerate(zip(raw_chunks, encoded)):
                chunk = DocumentChunk(
                    text=chunk_text,
                    chunk_id=i,
                    metadata={**base_metadata, "chunk_index": i},
                    embedding=emb,
                )
                chunks.append(chunk)
                embeddings_list.append(emb)
            self._chunks = chunks
            self._embeddings_matrix = np.array(embeddings_list)
        else:
            metadatas = [{**base_metadata, "chunk_index": i} for i in range(len(raw_chunks))]
            ids = [f"{source}_{i}" for i in range(len(raw_chunks))]
            self._get_store().upsert_documents(raw_chunks, metadatas=metadatas, ids=ids)

        logger.info("Indexed %d chunks from '%s' via %s backend", len(raw_chunks), source, self.backend)
        return len(raw_chunks)

    def load_from_file(
        self,
        file_path: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> int:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Document not found: {file_path}")
        ext = os.path.splitext(file_path)[1].lower()
        text = self._read_pdf(file_path) if ext == ".pdf" else self._read_text(file_path)
        return self.load_document(text, source=os.path.basename(file_path), metadata=metadata)

    def retrieve(
        self,
        query: str,
        top_k: int = 3,
        min_similarity: float = 0.15,
    ) -> List[Tuple[DocumentChunk, float]]:
        """Retrieve the most relevant chunks for a query."""
        if not self.is_ready:
            logger.warning("Retriever has no indexed documents")
            return []

        if self.backend == "memory":
            model = _get_model()
            query_embedding = model.encode([query], normalize_embeddings=True)[0]
            similarities = self._embeddings_matrix @ query_embedding
            top_indices = np.argsort(similarities)[::-1][:top_k]
            results: List[Tuple[DocumentChunk, float]] = []
            for idx in top_indices:
                score = float(similarities[idx])
                if score >= min_similarity:
                    results.append((self._chunks[idx], score))
            return results
        else:
            search_results = self._get_store().similarity_search(query, top_k=top_k, min_similarity=min_similarity)
            out: List[Tuple[DocumentChunk, float]] = []
            for i, sr in enumerate(search_results):
                chunk = DocumentChunk(
                    text=sr.text,
                    chunk_id=i,
                    metadata=sr.metadata,
                )
                out.append((chunk, sr.score))
            return out

    def retrieve_requirements(
        self,
        candidate_skills: List[str],
        top_k: int = 5,
    ) -> List[Tuple[DocumentChunk, float, str]]:
        if not candidate_skills:
            return []
        per_skill = max(2, top_k // len(candidate_skills))
        all_results: List[Tuple[DocumentChunk, float, str]] = []
        seen_ids: set = set()
        for skill in candidate_skills:
            query = f"job requirement experience {skill}"
            for chunk, score in self.retrieve(query, top_k=per_skill):
                if chunk.chunk_id not in seen_ids:
                    seen_ids.add(chunk.chunk_id)
                    all_results.append((chunk, score, skill))
        all_results.sort(key=lambda x: x[1], reverse=True)
        return all_results[:top_k]

    def get_all_text(self) -> str:
        return "\n\n".join(chunk.text for chunk in self._chunks)

    def clear(self) -> None:
        if self.backend == "memory":
            self._chunks = []
            self._embeddings_matrix = None
        else:
            self._get_store().clear()

    # ── Internal helpers ───────────────────────────────────────────────────────

    def _clean_text(self, text: str) -> str:
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r" {2,}", " ", text)
        return text.strip()

    def _split_into_chunks(self, text: str) -> List[str]:
        if len(text) <= self.chunk_size:
            return [text]
        sentences = re.split(r"(?<=[.!?])\s+", text)
        chunks: List[str] = []
        current = ""
        for sentence in sentences:
            if len(current) + len(sentence) + 1 <= self.chunk_size:
                current = f"{current} {sentence}".strip() if current else sentence
            else:
                if current:
                    chunks.append(current)
                if len(sentence) > self.chunk_size:
                    for i in range(0, len(sentence), self.chunk_size - self.chunk_overlap):
                        chunks.append(sentence[i: i + self.chunk_size])
                    current = ""
                else:
                    current = sentence
        if current:
            chunks.append(current)
        if self.chunk_overlap > 0 and len(chunks) > 1:
            overlapped = [chunks[0]]
            for i in range(1, len(chunks)):
                prev_tail = chunks[i - 1][-self.chunk_overlap:]
                overlapped.append(f"{prev_tail} {chunks[i]}".strip())
            chunks = overlapped
        return chunks

    @staticmethod
    def _read_text(file_path: str) -> str:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()

    @staticmethod
    def _read_pdf(file_path: str) -> str:
        try:
            import pdfplumber
            parts: List[str] = []
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        parts.append(page_text)
            return "\n\n".join(parts)
        except ImportError:
            pass
        try:
            from PyPDF2 import PdfReader
            reader = PdfReader(file_path)
            return "\n\n".join(page.extract_text() or "" for page in reader.pages)
        except ImportError as exc:
            raise ImportError("Install pdfplumber or PyPDF2 to read PDF files") from exc
