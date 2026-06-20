"""WebSocket endpoints for real-time interview and copilot updates."""

import asyncio
import json
import logging

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from app.core.websocket import interview_manager, copilot_manager
from app.core.ws_auth import ws_auth_required

logger = logging.getLogger(__name__)

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/interview/{interview_id}")
async def interview_ws(
    websocket: WebSocket,
    interview_id: str,
    token: str = Query(...),
):
    """WebSocket endpoint for real-time interview updates.
    
    Events received:
    - answer_submitted: When a candidate submits an answer
    - question_answered: When a question is marked as answered
    - interview_started: When interview transitions to in_progress
    - interview_paused: When interview is paused
    - interview_resumed: When interview is resumed
    - interview_closed: When interview is completed
    
    Events sent:
    - connected: Connection established
    - update: Real-time data update
    """
    auth_data = await ws_auth_required(websocket, token)
    user_id = auth_data["user_id"]
    
    await interview_manager.connect(interview_id, websocket)
    try:
        await interview_manager.broadcast(
            interview_id, "connected", {"user_id": user_id}
        )
        
        while True:
            try:
                data = await asyncio.wait_for(
                    websocket.receive_text(), timeout=60
                )
                message = json.loads(data)
                event_type = message.get("type", "")
                
                if event_type == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
                elif event_type == "subscribe":
                    await websocket.send_text(
                        json.dumps({"type": "subscribed", "channel": interview_id})
                    )
                else:
                    await interview_manager.broadcast(
                        interview_id, "message", {"from": user_id, **message}
                    )
                    
            except asyncio.TimeoutError:
                try:
                    await websocket.send_text(json.dumps({"type": "keepalive"}))
                except Exception:
                    break
            except json.JSONDecodeError:
                await websocket.send_text(
                    json.dumps({"type": "error", "detail": "Invalid JSON"})
                )
                
    except WebSocketDisconnect:
        logger.info(f"Interview WS disconnected: user={user_id} interview={interview_id}")
    except Exception as e:
        logger.error(f"Interview WS error: {e}")
    finally:
        interview_manager.disconnect(interview_id, websocket)


@router.websocket("/ws/copilot/{interview_id}")
async def copilot_ws(
    websocket: WebSocket,
    interview_id: str,
    token: str = Query(...),
):
    """WebSocket endpoint for real-time copilot assistance.
    
    Events received:
    - get_suggestions: Request new suggestions
    - dismiss_suggestion: Dismiss a suggestion
    
    Events sent:
    - connected: Connection established
    - suggestions: New suggestions generated
    - suggestion_dismissed: Confirmation of dismissal
    """
    auth_data = await ws_auth_required(websocket, token)
    user_id = auth_data["user_id"]
    
    await copilot_manager.connect(interview_id, websocket)
    try:
        await copilot_manager.broadcast(
            interview_id, "connected", {"user_id": user_id}
        )
        
        while True:
            try:
                data = await asyncio.wait_for(
                    websocket.receive_text(), timeout=60
                )
                message = json.loads(data)
                event_type = message.get("type", "")
                
                if event_type == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
                    
                elif event_type == "get_suggestions":
                    await websocket.send_text(
                        json.dumps({"type": "suggestions_loading"})
                    )
                    
                    # Generate suggestions (simplified for WebSocket)
                    # In production, this would query the DB and call AI service
                    await websocket.send_text(
                        json.dumps({
                            "type": "suggestions",
                            "suggestions": [
                                {
                                    "id": "ws-suggestion-1",
                                    "text": "Consider asking a follow-up question about their experience.",
                                    "category": "follow_up",
                                    "confidence": 0.85,
                                },
                                {
                                    "id": "ws-suggestion-2",
                                    "text": "The candidate's response shows good technical understanding.",
                                    "category": "assessment",
                                    "confidence": 0.78,
                                },
                            ],
                        })
                    )
                    
                elif event_type == "dismiss_suggestion":
                    suggestion_id = message.get("suggestion_id")
                    await websocket.send_text(
                        json.dumps({
                            "type": "suggestion_dismissed",
                            "suggestion_id": suggestion_id,
                        })
                    )
                    
                else:
                    await copilot_manager.broadcast(
                        interview_id, "message", {"from": user_id, **message}
                    )
                    
            except asyncio.TimeoutError:
                try:
                    await websocket.send_text(json.dumps({"type": "keepalive"}))
                except Exception:
                    break
            except json.JSONDecodeError:
                await websocket.send_text(
                    json.dumps({"type": "error", "detail": "Invalid JSON"})
                )
                
    except WebSocketDisconnect:
        logger.info(f"Copilot WS disconnected: user={user_id} interview={interview_id}")
    except Exception as e:
        logger.error(f"Copilot WS error: {e}")
    finally:
        copilot_manager.disconnect(interview_id, websocket)
