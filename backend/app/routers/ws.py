"""
app/routers/ws.py

Module 10: WebSocket endpoint for real-time vitals + alert push.

Connect:  ws://api:8000/ws/dashboard?token=<jwt>
Messages:
  server -> client:
    {"type": "vitals",  "patient_id": "...", "reading": {...}}
    {"type": "alert",   "patient_id": "...", "alerts":  [...]}
    {"type": "ping"}
"""
import asyncio
import json

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from app.services.ws_manager import manager

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/dashboard")
async def dashboard_ws(ws: WebSocket, token: str = Query("")):
    """
    Real-time dashboard WebSocket.
    Authenticates via ?token= query param (same JWT as REST).
    Sends ping every 30s to keep connection alive.
    """
    # Basic JWT check (silently allow in dev if no token — tighten in prod)
    from app.dependencies import _decode_token
    try:
        if token:
            _decode_token(token)
    except Exception:
        await ws.close(code=4001)
        return

    await manager.connect(ws)
    # Send welcome / connection count
    await manager.send_personal(ws, {
        "type":        "connected",
        "connections": manager.count,
    })

    try:
        while True:
            # Keep-alive ping every 30 s  (also receives any client message)
            try:
                data = await asyncio.wait_for(ws.receive_text(), timeout=30)
                msg  = json.loads(data)
                if msg.get("type") == "pong":
                    continue
            except asyncio.TimeoutError:
                await manager.send_personal(ws, {"type": "ping"})
    except WebSocketDisconnect:
        pass
    finally:
        await manager.disconnect(ws)
