from __future__ import annotations

import json
from typing import Any

from fastapi import WebSocket


class EscalationManager:
    """Manages WebSocket connections for real-time escalation events."""

    def __init__(self) -> None:
        self._connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections.append(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        if websocket in self._connections:
            self._connections.remove(websocket)

    @property
    def active_connections(self) -> int:
        return len(self._connections)

    async def broadcast(self, event: dict[str, Any]) -> None:
        """Broadcast an escalation event to all connected clients."""
        message = json.dumps(event)
        disconnected = []
        for ws in self._connections:
            try:
                await ws.send_text(message)
            except Exception:
                disconnected.append(ws)
        for ws in disconnected:
            self.disconnect(ws)


# Singleton instances
escalation_manager = EscalationManager()
decision_manager = EscalationManager()  # Reuse same class — broadcasts all gate decisions
