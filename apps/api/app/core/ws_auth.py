"""WebSocket token authentication."""

import logging
from typing import Optional
from fastapi import Query, WebSocket
from starlette.websockets import WebSocketDisconnect
from jose import JWTError

from app.core.security import verify_token

logger = logging.getLogger(__name__)


async def ws_auth(token: str = Query(...)) -> Optional[dict]:
    """Validate JWT token passed as query parameter for WebSocket connections.
    
    Args:
        token: JWT token from query parameter
        
    Returns:
        Token payload dict if valid, None if invalid
    """
    try:
        payload = verify_token(token)
        user_id = payload.get("sub")
        if not user_id:
            logger.warning("WS auth failed: no subject in token")
            return None
        return {"user_id": user_id, "payload": payload}
    except JWTError as e:
        logger.warning(f"WS auth failed: {e}")
        return None
    except Exception as e:
        logger.error(f"WS auth error: {e}")
        return None


async def ws_auth_required(websocket: WebSocket, token: str = Query(...)) -> dict:
    """Strict WebSocket auth that closes connection if invalid.
    
    Args:
        websocket: The WebSocket connection
        token: JWT token from query parameter
        
    Returns:
        Token payload dict if valid
        
    Raises:
        WebSocketDisconnect: If authentication fails
    """
    auth_data = await ws_auth(token)
    if not auth_data:
        await websocket.close(code=4001, reason="Invalid or missing token")
        raise WebSocketDisconnect(code=4001)
    return auth_data
