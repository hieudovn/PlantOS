"""Heartbeat — report edge node health to Center."""

import logging
import asyncio
import httpx

logger = logging.getLogger(__name__)


class HealthReporter:
    def __init__(self, heartbeat_url: str, edge_node_id: str, interval: int = 10):
        self.url = heartbeat_url
        self.node_id = edge_node_id
        self.interval = interval

    async def send_heartbeat(self, status: str = "online", backlog: int = 0):
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                await client.post(self.url, json={
                    "edge_node_id": self.node_id,
                    "status": status,
                    "backlog_count": backlog,
                })
        except Exception as e:
            logger.warning(f"Heartbeat failed: {e}")

    async def run(self, get_backlog_fn):
        """Send heartbeats periodically."""
        while True:
            backlog = get_backlog_fn()
            await self.send_heartbeat("online", backlog)
            await asyncio.sleep(self.interval)
