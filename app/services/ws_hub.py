"""
WebSocketHub — in-process pub/sub broadcast for real-time push to the frontend.

Topics:
  "analytics"       — all analytics events emitted by AnalyticsProcessor
  "camera:{id}"     — per-camera detection count updates (live headcount)

Usage (inside a FastAPI WebSocket endpoint):
    await hub.subscribe(ws, "camera:1")
    try:
        while True:
            await ws.receive_text()   # keep-alive / absorb pings
    except WebSocketDisconnect:
        pass
    finally:
        await hub.unsubscribe(ws, "camera:1")

The broadcast() method is fire-and-forget — it silently removes any socket
that raises an error during send (disconnected clients clean themselves up).
"""

import asyncio
import logging
from collections import defaultdict
from typing import Dict, Set

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class WebSocketHub:
    def __init__(self):
        # topic → set of active WebSocket connections
        self._subs: Dict[str, Set[WebSocket]] = defaultdict(set)
        self._lock = asyncio.Lock()

    async def subscribe(self, ws: WebSocket, topic: str) -> None:
        async with self._lock:
            self._subs[topic].add(ws)
        logger.debug("WS subscribe  topic=%s  total=%d", topic, len(self._subs[topic]))

    async def unsubscribe(self, ws: WebSocket, topic: str) -> None:
        async with self._lock:
            self._subs[topic].discard(ws)
        logger.debug("WS unsubscribe topic=%s  total=%d", topic, len(self._subs[topic]))

    async def broadcast(self, topic: str, data: dict) -> None:
        """Send *data* as JSON to every subscriber of *topic*.

        Dead sockets are silently removed; this never raises.
        """
        async with self._lock:
            sockets = set(self._subs.get(topic, set()))

        if not sockets:
            return

        dead: Set[WebSocket] = set()
        for ws in sockets:
            try:
                await ws.send_json(data)
            except Exception:
                dead.add(ws)

        if dead:
            async with self._lock:
                self._subs[topic] -= dead
            logger.debug("WS cleaned %d dead socket(s) on topic=%s", len(dead), topic)

    def subscriber_count(self, topic: str) -> int:
        return len(self._subs.get(topic, set()))
