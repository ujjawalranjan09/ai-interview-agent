"""Per-session interview memory store using Chroma.

Architecture Improvement #2: persists every Q&A pair, emotion state,
and score per answer so that:

  - The adaptive generator can retrieve the *full session context*
    (not just the last answer) when deciding the next question.
  - The coaching module can query past sessions for a candidate to
    detect persistent weaknesses.
  - The analytics module can visualise confidence trends across sessions.

Collection layout
-----------------
  ``interview_memory``   — one document per answer (text = Q + A)
    metadata keys: session_id, candidate_id, question_index,
                   confidence_score, emotion_label, skill_target,
                   difficulty, timestamp

The store is keyed by ``session_id`` so multiple candidates never
share the same vector space.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

COLLECTION_NAME = "interview_memory"
_DEFAULT_EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


class SessionStore:
    """Persistent per-session interview memory backed by Chroma.

    Parameters
    ----------
    session_id:
        UUID string for the current interview session.
    candidate_id:
        Stable identifier for the candidate (e.g. MongoDB _id).
    persist_path:
        Chroma DB directory on disk.
    """

    def __init__(
        self,
        session_id: Optional[str] = None,
        candidate_id: str = "unknown",
        persist_path: str = "database/chroma",
        embed_model: str = _DEFAULT_EMBED_MODEL,
    ) -> None:
        import chromadb  # noqa: PLC0415
        from chromadb.utils.embedding_functions import (
            SentenceTransformerEmbeddingFunction,  # noqa: PLC0415
        )

        self.session_id = session_id or str(uuid.uuid4())
        self.candidate_id = candidate_id
        self.client = chromadb.PersistentClient(path=persist_path)
        self._embed_fn = SentenceTransformerEmbeddingFunction(model_name=embed_model)
        self._collection = self.client.get_or_create_collection(
            name=COLLECTION_NAME,
            embedding_function=self._embed_fn,
        )
        logger.info(
            "SessionStore ready | session=%s candidate=%s store=%s",
            self.session_id, self.candidate_id, persist_path,
        )

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def store_answer(
        self,
        question: str,
        answer: str,
        question_index: int,
        confidence_score: float,
        emotion_label: str,
        skill_target: str = "general",
        difficulty: str = "medium",
    ) -> str:
        """Persist a single Q&A pair with all metadata.

        Returns the document ID.
        """
        doc_id = f"{self.session_id}-q{question_index}"
        document_text = f"Q: {question}\nA: {answer}"

        self._collection.upsert(
            ids=[doc_id],
            documents=[document_text],
            metadatas=[{
                "session_id": self.session_id,
                "candidate_id": self.candidate_id,
                "question_index": question_index,
                "confidence_score": round(confidence_score, 2),
                "emotion_label": emotion_label,
                "skill_target": skill_target,
                "difficulty": difficulty,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }],
        )
        logger.debug("Stored answer %s (conf=%.1f)", doc_id, confidence_score)
        return doc_id

    # ------------------------------------------------------------------
    # Read — current session
    # ------------------------------------------------------------------

    def get_session_history(self, n_last: int = 10) -> List[Dict[str, Any]]:
        """Retrieve the last N answers for the current session."""
        result = self._collection.get(
            where={"session_id": self.session_id},
            include=["documents", "metadatas"],
        )
        items = list(zip(result["documents"], result["metadatas"]))
        # Sort by question_index ascending
        items.sort(key=lambda x: x[1].get("question_index", 0))
        return [
            {"text": doc, "metadata": meta}
            for doc, meta in items[-n_last:]
        ]

    def get_context_chunks(self, query: str, n_results: int = 5) -> List[str]:
        """Semantic search over current session for adaptive generator context."""
        result = self._collection.query(
            query_texts=[query],
            n_results=n_results,
            where={"session_id": self.session_id},
        )
        return result.get("documents", [[]])[0]

    def get_confidence_timeline(self) -> List[float]:
        """Return ordered list of confidence scores for this session."""
        history = self.get_session_history(n_last=100)
        return [item["metadata"].get("confidence_score", 0.0) for item in history]

    # ------------------------------------------------------------------
    # Read — cross-session (candidate history)
    # ------------------------------------------------------------------

    def get_candidate_weak_areas(
        self, confidence_threshold: float = 45.0, n_results: int = 20
    ) -> List[Dict[str, Any]]:
        """Retrieve low-confidence answers across ALL sessions for this candidate.

        Used by the coaching module to identify persistent skill gaps.
        """
        result = self._collection.get(
            where={"candidate_id": self.candidate_id},
            include=["documents", "metadatas"],
        )
        weak = [
            {"text": doc, "metadata": meta}
            for doc, meta in zip(result["documents"], result["metadatas"])
            if meta.get("confidence_score", 100.0) < confidence_threshold
        ]
        weak.sort(key=lambda x: x["metadata"].get("confidence_score", 0.0))
        return weak[:n_results]

    def get_candidate_session_ids(self) -> List[str]:
        """Return all unique session IDs for this candidate."""
        result = self._collection.get(
            where={"candidate_id": self.candidate_id},
            include=["metadatas"],
        )
        seen: set[str] = set()
        ids: list[str] = []
        for meta in result["metadatas"]:
            sid = meta.get("session_id", "")
            if sid and sid not in seen:
                seen.add(sid)
                ids.append(sid)
        return ids
