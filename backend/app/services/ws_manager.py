"""
app/services/ws_manager.py

WebSocket connection manager for Module 10.
All connected doctors receive real-time vitals + alert broadcasts.
"""
import asyncio
import json
from typing import Any

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        self._connections: list[WebSocket] = []
        self._lock = asyncio.Lock()

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        async with self._lock:
            self._connections.append(ws)

    async def disconnect(self, ws: WebSocket) -> None:
        async with self._lock:
            self._connections = [c for c in self._connections if c is not ws]

    async def broadcast(self, payload: dict[str, Any]) -> None:
        """Send JSON payload to all connected clients; silently drop closed sockets."""
        msg = json.dumps(payload, default=str)
        dead: list[WebSocket] = []
        for ws in list(self._connections):
            try:
                await ws.send_text(msg)
            except Exception:
                dead.append(ws)
        if dead:
            async with self._lock:
                self._connections = [c for c in self._connections if c not in dead]

    async def send_personal(self, ws: WebSocket, payload: dict[str, Any]) -> None:
        await ws.send_text(json.dumps(payload, default=str))

    @property
    def count(self) -> int:
        return len(self._connections)


# Singleton — import this everywhere
manager = ConnectionManager()
