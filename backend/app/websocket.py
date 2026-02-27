from __future__ import annotations

import asyncio
import json
from typing import Any

from fastapi import WebSocket

MAX_CONNECTIONS = 100


class BroadcastManager:
    """Manages WebSocket connections with connection limits and non-blocking broadcast."""

    def __init__(self, max_connections: int = MAX_CONNECTIONS) -> None:
        self._connections: list[WebSocket] = []
        self._max_connections = max_connections

    async def connect(self, websocket: WebSocket) -> bool:
        """Accept a connection. Returns False if limit reached."""
        if len(self._connections) >= self._max_connections:
            await websocket.close(code=1013, reason="Maximum connections reached")
            return False
        await websocket.accept()
        self._connections.append(websocket)
        return True

    def disconnect(self, websocket: WebSocket) -> None:
        if websocket in self._connections:
            self._connections.remove(websocket)

    @property
    def active_connections(self) -> int:
        return len(self._connections)

    async def broadcast(self, event: dict[str, Any]) -> None:
        """Broadcast event to all connected clients (non-blocking)."""
        if not self._connections:
            return
        message = json.dumps(event)
        disconnected = []
        for ws in self._connections:
            try:
                await asyncio.wait_for(ws.send_text(message), timeout=5.0)
            except Exception:
                disconnected.append(ws)
        for ws in disconnected:
            self.disconnect(ws)

    def fire_and_forget(self, event: dict[str, Any]) -> None:
        """Schedule broadcast as a background task (does not block caller)."""
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self.broadcast(event))
        except RuntimeError:
            pass  # No event loop — skip silently


# Backwards compat
EscalationManager = BroadcastManager

# Singleton instances
escalation_manager = BroadcastManager()
decision_manager = BroadcastManager()
