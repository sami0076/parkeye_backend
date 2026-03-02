"""
WebSocket hub — broadcasts lot occupancy to all connected iOS clients every 30 s.

The ConnectionManager is a module-level singleton shared between the router
(accept / disconnect) and the background broadcaster task (started in main.py
lifespan).
"""

from __future__ import annotations

import asyncio
import json
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.database import AsyncSessionLocal
from app.services.occupancy import get_lots_with_current_occupancy

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ws", tags=["websocket"])


class ConnectionManager:
    """Tracks active WebSocket connections and broadcasts JSON payloads."""

    def __init__(self) -> None:
        self.active_connections: set[WebSocket] = set()

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        self.active_connections.add(ws)

    def disconnect(self, ws: WebSocket) -> None:
        self.active_connections.discard(ws)

    async def broadcast(self, payload: str) -> None:
        closed: list[WebSocket] = []
        for ws in self.active_connections:
            try:
                await ws.send_text(payload)
            except Exception:
                closed.append(ws)
        for ws in closed:
            self.active_connections.discard(ws)


manager = ConnectionManager()


@router.websocket("/occupancy")
async def occupancy_ws(ws: WebSocket):
    """Accept a client and keep the connection alive until disconnect."""
    await manager.connect(ws)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(ws)


async def _broadcast_loop() -> None:
    """Background task: query DB every 30 s and push occupancy to all clients."""
    while True:
        try:
            async with AsyncSessionLocal() as db:
                rows = await get_lots_with_current_occupancy(db)
            payload = json.dumps([
                {
                    "lot_id": row["lot"].id,
                    "occupancy_pct": row["occupancy_pct"],
                    "color": row["color"],
                }
                for row in rows
            ])
            await manager.broadcast(payload)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("occupancy broadcast error")
        await asyncio.sleep(30)
