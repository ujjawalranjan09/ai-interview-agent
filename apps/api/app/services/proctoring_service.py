"""Proctoring service — AI proctoring session management."""

import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.proctoring import ProctoringSession, ProctoringEvent


async def start_session(
    db: AsyncSession,
    interview_id: uuid.UUID,
    config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    session = ProctoringSession(
        interview_id=interview_id,
        status="active",
        started_at=datetime.utcnow(),
        config=config or {},
    )
    db.add(session)
    await db.flush()
    return {
        "id": str(session.id),
        "interview_id": str(session.interview_id),
        "status": session.status,
        "started_at": session.started_at.isoformat(),
    }


async def end_session(
    db: AsyncSession, session_id: uuid.UUID
) -> Dict[str, Any]:
    result = await db.execute(
        select(ProctoringSession).where(ProctoringSession.id == session_id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise ValueError("Proctoring session not found")

    session.status = "ended"
    session.ended_at = datetime.utcnow()

    events_result = await db.execute(
        select(ProctoringEvent).where(
            ProctoringEvent.session_id == session_id,
            ProctoringEvent.severity.in_(["high", "medium"]),
        )
    )
    flags = list(events_result.scalars().all())
    session.flags_total = len(flags)
    session.risk_score = min(1.0, sum(f.confidence for f in flags if f.confidence) / max(len(flags), 1))

    await db.flush()
    return {
        "id": str(session.id),
        "status": "ended",
        "flags_total": session.flags_total,
        "risk_score": session.risk_score,
    }


async def log_event(
    db: AsyncSession,
    session_id: uuid.UUID,
    event_type: str,
    severity: str = "info",
    confidence: float = 0.0,
    details: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    event = ProctoringEvent(
        session_id=session_id,
        event_type=event_type,
        severity=severity,
        confidence=confidence,
        details=details or {},
        timestamp=datetime.utcnow(),
    )
    db.add(event)
    await db.flush()

    result = await db.execute(
        select(ProctoringSession).where(ProctoringSession.id == session_id)
    )
    session = result.scalar_one_or_none()
    if session and session.status == "active":
        session.flags_total += 1

    await db.flush()
    return {
        "id": str(event.id),
        "event_type": event.event_type,
        "severity": event.severity,
    }


async def get_session(
    db: AsyncSession, session_id: uuid.UUID
) -> Optional[Dict[str, Any]]:
    result = await db.execute(
        select(ProctoringSession).where(ProctoringSession.id == session_id)
    )
    session = result.scalar_one_or_none()
    if not session:
        return None

    events_result = await db.execute(
        select(ProctoringEvent)
        .where(ProctoringEvent.session_id == session_id)
        .order_by(ProctoringEvent.timestamp.desc())
        .limit(50)
    )
    events = events_result.scalars().all()

    return {
        "id": str(session.id),
        "interview_id": str(session.interview_id),
        "status": session.status,
        "started_at": session.started_at.isoformat(),
        "ended_at": session.ended_at.isoformat() if session.ended_at else None,
        "flags_total": session.flags_total,
        "risk_score": session.risk_score,
        "events": [
            {
                "id": str(e.id),
                "event_type": e.event_type,
                "severity": e.severity,
                "confidence": e.confidence,
                "details": e.details,
                "timestamp": e.timestamp.isoformat(),
            }
            for e in events
        ],
    }


async def list_sessions(
    db: AsyncSession,
    interview_id: Optional[uuid.UUID] = None,
    page: int = 1,
    page_size: int = 20,
) -> Dict[str, Any]:
    stmt = select(ProctoringSession)
    if interview_id:
        stmt = stmt.where(ProctoringSession.interview_id == interview_id)
    stmt = stmt.order_by(ProctoringSession.created_at.desc())
    stmt = stmt.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(stmt)
    sessions = result.scalars().all()

    return {
        "items": [
            {
                "id": str(s.id),
                "interview_id": str(s.interview_id),
                "status": s.status,
                "started_at": s.started_at.isoformat(),
                "flags_total": s.flags_total,
                "risk_score": s.risk_score,
            }
            for s in sessions
        ],
        "total": len(sessions),
        "page": page,
        "page_size": page_size,
    }
