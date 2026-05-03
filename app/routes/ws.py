"""
WebSocket endpoints for real-time push to the frontend.

Endpoints (all under /ws/):
  WS /ws/analytics                  — stream all analytics events, optional ?camera_id= filter
  WS /ws/cameras/{camera_id}/live   — stream per-camera detection count

The hub instance is injected by main.py:
    import app.routes.ws as ws_routes
    ws_routes.hub = hub
"""

import logging
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.services.ws_hub import WebSocketHub

logger = logging.getLogger(__name__)

router = APIRouter()

# Injected by main.py after hub is created.
hub: Optional[WebSocketHub] = None


@router.websocket("/ws/analytics")
async def ws_analytics(websocket: WebSocket, camera_id: Optional[int] = None):
    """
    Stream analytics events to the client.
    If camera_id is provided, only events for that camera are forwarded.
    """
    if hub is None:
        await websocket.close(code=1013)  # try again later
        return

    await websocket.accept()
    topic = "analytics"
    await hub.subscribe(websocket, topic)
    logger.info("WS /ws/analytics connected (camera_id=%s)", camera_id)
    try:
        while True:
            # Keep-alive: client may send pings; we just absorb them.
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    except Exception as exc:
        logger.debug("WS /ws/analytics error: %s", exc)
    finally:
        await hub.unsubscribe(websocket, topic)
        logger.info("WS /ws/analytics disconnected (camera_id=%s)", camera_id)


@router.websocket("/ws/cameras/{camera_id}/live")
async def ws_camera_live(websocket: WebSocket, camera_id: int):
    """
    Stream live detection count for a single camera.
    Message shape: {"type": "detections", "camera_id": int, "count": int, "ts": int}
    """
    if hub is None:
        await websocket.close(code=1013)
        return

    await websocket.accept()
    topic = f"camera:{camera_id}"
    await hub.subscribe(websocket, topic)
    logger.info("WS /ws/cameras/%d/live connected", camera_id)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    except Exception as exc:
        logger.debug("WS /ws/cameras/%d/live error: %s", camera_id, exc)
    finally:
        await hub.unsubscribe(websocket, topic)
        logger.info("WS /ws/cameras/%d/live disconnected", camera_id)
