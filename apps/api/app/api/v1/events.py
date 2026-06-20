"""SSE events endpoint for real-time interview updates."""

import asyncio
import json
import uuid
from typing import Dict

from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse

from app.core.security import verify_token

router = APIRouter(tags=["events"])

# In-memory event queues per interview
_event_queues: Dict[uuid.UUID, list[asyncio.Queue]] = {}


async def broadcast_event(interview_id: uuid.UUID, event_type: str, data: dict):
    """Push an event to all connected clients for an interview."""
    queues = _event_queues.get(interview_id, [])
    message = f"event: {event_type}\ndata: {json.dumps(data)}\n\n"
    for q in queues:
        try:
            await q.put(message)
        except Exception:
            pass


@router.get("/interviews/{interview_id}/events")
async def interview_events(
    interview_id: uuid.UUID,
    token: str = Query(...),
):
    # Authenticate via query param (EventSource can't set headers)
    try:
        verify_token(token)
    except Exception:
        return StreamingResponse(
            iter(['event: error\ndata: {"detail":"Invalid token"}\n\n']),
            media_type="text/event-stream",
            status_code=401,
        )

    queue: asyncio.Queue = asyncio.Queue()
    _event_queues.setdefault(interview_id, []).append(queue)

    async def event_stream():
        try:
            yield f'event: connected\ndata: {json.dumps({"interview_id": str(interview_id)})}\n\n'
            while True:
                try:
                    message = await asyncio.wait_for(queue.get(), timeout=30)
                    yield message
                except asyncio.TimeoutError:
                    yield ": keepalive\n\n"
        finally:
            if interview_id in _event_queues:
                try:
                    _event_queues[interview_id].remove(queue)
                except ValueError:
                    pass

    return StreamingResponse(event_stream(), media_type="text/event-stream")
