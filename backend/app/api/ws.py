"""WebSocket endpoint for real-time measurement updates."""

import asyncio
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()

# Connected clients
_clients: set[WebSocket] = set()


@router.websocket("/ws/measurements")
async def ws_measurements(ws: WebSocket):
    await ws.accept()
    _clients.add(ws)
    try:
        while True:
            # Keep-alive: wait for any message or ping
            await ws.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        _clients.discard(ws)


async def broadcast_measurements(measurements: list[dict]):
    """Broadcast new measurements to all connected WebSocket clients."""
    if not _clients:
        return
    payload = json.dumps({"type": "measurements", "data": measurements})
    dead: set[WebSocket] = set()
    for ws in _clients:
        try:
            await ws.send_text(payload)
        except Exception:
            dead.add(ws)
    _clients -= dead
