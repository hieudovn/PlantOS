"""OPC UA collector — poll NodeIds, normalize, write to DuckDB.

Supports multiple endpoints via MultiOpcUaCollector wrapper.
"""

import asyncio
import logging
from datetime import datetime, timezone

from .client import OpcUaClient
from .mapper import OpcUaMapper

logger = logging.getLogger(__name__)


class OpcUaCollector:
    """Polls a single OPC UA server periodically, maps values, writes to local buffer."""

    def __init__(self, config: dict, buffer):
        self.config = config
        self.buffer = buffer
        self.client = OpcUaClient(
            endpoint=config.get("endpoint", "opc.tcp://127.0.0.1:4840"),
            timeout=config.get("timeout", 5.0),
        )
        self.mapper = OpcUaMapper(config.get("tags", []))
        self.interval = config.get("poll_interval_ms", 1000) / 1000
        self._enabled = config.get("enabled", False)
        self._task: asyncio.Task | None = None

    @property
    def connected(self) -> bool:
        return self.client.is_connected

    @property
    def signal_count(self) -> int:
        return len(self.mapper.node_ids)

    async def start(self):
        if not self._enabled:
            logger.info(f"OPC UA collector disabled ({self.config.get('endpoint', '?')})")
            return

        connected = await self.client.connect()
        if not connected:
            logger.warning(f"OPC UA collector: initial connection failed, retrying ({self.config.get('endpoint', '?')})")
            self._task = asyncio.create_task(self._retry_connect())
            return

        logger.info(f"OPC UA collector started ({self.signal_count} signals @ {self.config.get('endpoint', '?')})")
        self._task = asyncio.create_task(self._poll_loop())

    async def _retry_connect(self):
        while not self.client.is_connected:
            await asyncio.sleep(10)
            await self.client.connect()

    async def _poll_loop(self):
        while self.client.is_connected:
            try:
                raw = await self.client.read_values(self.mapper.node_ids)
                if raw:
                    measurements = self.mapper.map_values(raw)
                    if measurements:
                        now = datetime.now(timezone.utc)
                        rows = [
                            {
                                "timestamp": now.isoformat(),
                                "signal_id": m["signal_id"],
                                "value": m["value"],
                                "quality": "GOOD",
                                "source": "opcua",
                            }
                            for m in measurements
                        ]
                        self.buffer.write(rows)
            except Exception as e:
                logger.error(f"OPC UA poll error ({self.config.get('endpoint', '?')}): {e}")
            await asyncio.sleep(self.interval)

    async def stop(self):
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        await self.client.disconnect()


class MultiOpcUaCollector:
    """Manages multiple OPC UA collector endpoints."""

    def __init__(self):
        self.collectors: list[OpcUaCollector] = []

    def add_collector(self, config: dict, buffer):
        """Add an OPC UA endpoint collector."""
        collector = OpcUaCollector(config, buffer)
        self.collectors.append(collector)
        return collector

    async def start_all(self):
        """Start all collectors concurrently."""
        tasks = [c.start() for c in self.collectors if c._enabled]
        if tasks:
            await asyncio.gather(*tasks)

    @property
    def status_list(self) -> list[dict]:
        """Return status for each endpoint."""
        return [
            {
                "enabled": c._enabled,
                "connected": c.connected,
                "endpoint": c.config.get("endpoint", ""),
                "signal_count": c.signal_count,
            }
            for c in self.collectors
        ]

    @property
    def total_signals(self) -> int:
        return sum(c.signal_count for c in self.collectors if c._enabled)

    @property
    def any_connected(self) -> bool:
        return any(c.connected for c in self.collectors)
