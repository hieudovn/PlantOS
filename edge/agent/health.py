"""Heartbeat — report edge node health to Center."""

import logging
import asyncio
import socket
import httpx

logger = logging.getLogger(__name__)

EDGE_VERSION = "0.1.0"


class HealthReporter:
    def __init__(self, heartbeat_url: str, edge_node_id: str, interval: int = 10,
                 api_key: str = "", bearer_token: str = "", get_signal_count_fn=None):
        self.url = heartbeat_url
        self.node_id = edge_node_id
        self.interval = interval
        self.api_key = api_key
        self.bearer_token = bearer_token
        self.hostname = socket.gethostname()
        self.ip_address = self._get_ip()
        self.get_signal_count_fn = get_signal_count_fn or (lambda: 0)

    def _get_ip(self) -> str:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"

    async def send_heartbeat(self, status: str = "online", backlog: int = 0):
        try:
            signal_count = self.get_signal_count_fn()
            async with httpx.AsyncClient(timeout=5) as client:
                headers = {}
                if self.bearer_token:
                    headers["Authorization"] = f"Bearer {self.bearer_token}"
                elif self.api_key:
                    headers["X-API-Key"] = self.api_key
                await client.post(self.url, json={
                    "edge_node_id": self.node_id,
                    "status": status,
                    "backlog_count": backlog,
                    "hostname": self.hostname,
                    "ip_address": self.ip_address,
                    "signal_count": signal_count,
                    "version": EDGE_VERSION,
                }, headers=headers)
        except Exception as e:
            logger.warning(f"Heartbeat failed: {e}")

    async def run(self, get_backlog_fn):
        """Send heartbeats periodically."""
        while True:
            backlog = get_backlog_fn()
            await self.send_heartbeat("online", backlog)
            await asyncio.sleep(self.interval)
