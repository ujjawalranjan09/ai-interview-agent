"""WebSocket ConnectionManager — manages real-time connections."""

import json
import logging
from typing import Dict, Set
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections by channel (e.g. interview_id or copilot_id)."""

    def __init__(self):
        self._channels: Dict[str, Set[WebSocket]] = {}

    async def connect(self, channel: str, websocket: WebSocket):
        await websocket.accept()
        self._channels.setdefault(channel, set()).add(websocket)
        logger.info(f"WS connected: channel={channel} total={len(self._channels[channel])}")

    def disconnect(self, channel: str, websocket: WebSocket):
        if channel in self._channels:
            self._channels[channel].discard(websocket)
            if not self._channels[channel]:
                del self._channels[channel]
        logger.info(f"WS disconnected: channel={channel}")

    async def broadcast(self, channel: str, event_type: str, data: dict):
        message = json.dumps({"type": event_type, **data})
        dead: list[WebSocket] = []
        for ws in self._channels.get(channel, set()):
            try:
                await ws.send_text(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self._channels.get(channel, set()).discard(ws)

    def channel_count(self, channel: str) -> int:
        return len(self._channels.get(channel, set()))

    def total_connections(self) -> int:
        return sum(len(s) for s in self._channels.values())


# Singleton instances
interview_manager = ConnectionManager()
copilot_manager = ConnectionManager()
