"""Resume + job description indexing pipeline.

Call ``index_candidate_materials`` at the start of an interview session
to populate the Chroma vector store for the session.
"""

from __future__ import annotations

from typing import Any, Dict

from modules.resume.candidate_profile import build_candidate_profile
from modules.rag.vector_store import InterviewVectorStore, chunk_text


def index_candidate_materials(
    resume_path: str = "",
    resume_text: str = "",
    job_description: str = "",
    persist_path: str = "database/chroma",
) -> Dict[str, Any]:
    """Build candidate profile and index all materials into Chroma.

    Returns a summary dict with profile data and chunk counts.
    """
    profile = build_candidate_profile(
        resume_path=resume_path, resume_text=resume_text
    )
    store = InterviewVectorStore(persist_path=persist_path)

    # ---- Index resume chunks ----------------------------------------
    resume_chunks = chunk_text(profile["resume_text"])
    resume_docs = [
        {
            "id": f"resume-{i}",
            "text": chunk,
            "metadata": {"source_type": "candidate_resume", "topic": "resume"},
        }
        for i, chunk in enumerate(resume_chunks)
    ]
    if resume_docs:
        store.add_documents("candidate_resume", resume_docs)

    # ---- Index job description ----------------------------------------
    jd_chunks: list[str] = []
    if job_description.strip():
        jd_chunks = chunk_text(job_description)
        jd_docs = [
            {
                "id": f"jd-{i}",
                "text": chunk,
                "metadata": {
                    "source_type": "job_description",
                    "topic": "job_description",
                },
            }
            for i, chunk in enumerate(jd_chunks)
        ]
        store.add_documents("job_description", jd_docs)

    return {
        "profile": profile,
        "indexed_resume_chunks": len(resume_docs),
        "indexed_jd_chunks": len(jd_chunks),
        "store_path": persist_path,
    }
