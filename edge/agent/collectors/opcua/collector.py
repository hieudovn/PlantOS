"""OPC UA collector — poll NodeIds, normalize, write to DuckDB."""

import asyncio
import logging
from datetime import datetime, timezone

from .client import OpcUaClient
from .mapper import OpcUaMapper

logger = logging.getLogger(__name__)


class OpcUaCollector:
    """Polls OPC UA server periodically, maps values, writes to local buffer."""

    def __init__(self, config: dict, buffer, mapper=None):
        self.config = config
        self.buffer = buffer
        self.client = OpcUaClient(
            endpoint=config.get("endpoint", "opc.tcp://127.0.0.1:4840"),
            timeout=config.get("timeout", 5.0),
        )
        self.mapper = mapper or OpcUaMapper(config.get("tags", []))
        self.interval = config.get("poll_interval_ms", 1000) / 1000
        self._enabled = config.get("enabled", False)
        self._task: asyncio.Task | None = None

    @property
    def connected(self) -> bool:
        return self.client.is_connected

    async def start(self):
        if not self._enabled:
            logger.info("OPC UA collector disabled")
            return

        connected = await self.client.connect()
        if not connected:
            logger.warning("OPC UA collector: initial connection failed, retrying...")
            self._task = asyncio.create_task(self._retry_connect())
            return

        logger.info(f"OPC UA collector started ({len(self.mapper.node_ids)} signals)")
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
                logger.error(f"OPC UA poll error: {e}")
            await asyncio.sleep(self.interval)

    async def stop(self):
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        await self.client.disconnect()
