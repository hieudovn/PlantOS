"""OPC UA Connector — implements BaseConnector for OPC UA protocol."""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any

from agent.connectors.base import (
    BaseConnector, ConnectorStatus, RawReading, TagConfig, TestResult,
)
from agent.connectors.opcua.client import OpcUaClient
from agent.connectors.opcua.mapper import OpcUaMapper

logger = logging.getLogger(__name__)


class OpcUaConnector(BaseConnector):
    """OPC UA connector — polls NodeIds, returns RawReadings.

    Refactored from edge/agent/collectors/opcua/ into BaseConnector interface.
    Supports reconnection with exponential backoff (1s→30s max).
    """

    def __init__(self, connector_id: str, config: dict):
        super().__init__(connector_id, config)
        self.connector_type = "opcua"
        conn = config.get("connection", {})
        self.client = OpcUaClient(
            endpoint=conn.get("endpoint", "opc.tcp://127.0.0.1:4840"),
            timeout=conn.get("timeout", 5.0),
        )
        tags_raw = config.get("tags", [])
        self.tags = [TagConfig(**t) if isinstance(t, dict) else t for t in tags_raw]
        self.mapper = OpcUaMapper(self.tags)
        self._interval = config.get("poll_interval_ms", 1000) / 1000
        self._task: asyncio.Task | None = None
        self._last_success: datetime | None = None
        self._last_error: str | None = None
        self._last_error_at: datetime | None = None

    async def validate_config(self, config: dict) -> list[str]:
        errors = []
        conn = config.get("connection", {})
        if not conn.get("endpoint"):
            errors.append("Missing 'connection.endpoint'")
        elif not conn["endpoint"].startswith("opc.tcp://"):
            errors.append("Invalid endpoint format — must start with opc.tcp://")
        return errors

    async def test_connection(self) -> TestResult:
        import time
        conn = self.config.get("connection", {})
        endpoint = conn.get("endpoint", "opc.tcp://127.0.0.1:4840")
        test_client = OpcUaClient(endpoint=endpoint, timeout=conn.get("timeout", 5.0))
        start = time.monotonic()
        ok = await test_client.connect()
        elapsed = (time.monotonic() - start) * 1000
        if ok:
            await test_client.disconnect()
            return TestResult(success=True, message="OPC UA server reachable",
                              latency_ms=round(elapsed, 1))
        return TestResult(success=False, message="OPC UA connection failed",
                          detail="Could not connect to endpoint", latency_ms=round(elapsed, 1))

    async def start(self):
        ok = await self.client.connect()
        if not ok:
            self._task = asyncio.create_task(self._reconnect_loop())
            return
        self._task = asyncio.create_task(self._poll_loop())

    async def stop(self):
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        await self.client.disconnect()
        self._running = False

    async def status(self) -> ConnectorStatus:
        return ConnectorStatus(
            connector_id=self.connector_id,
            type=self.connector_type,
            status="running" if self._running else "stopped",
            connected=self.client.is_connected,
            signal_count=len(self.tags),
            last_success_at=self._last_success,
            last_error=self._last_error,
            last_error_at=self._last_error_at,
        )

    async def read_tags(self, tag_configs: list[TagConfig]) -> list[RawReading]:
        raw = await self.client.read_values([t.source_ref for t in tag_configs if t.enabled])
        self.mapper.tags = tag_configs
        self.mapper.node_id_map = {t.source_ref: t for t in tag_configs}
        return self.mapper.map_values(raw)

    async def browse(self, path: str = "") -> list[dict[str, Any]]:
        ns = self.config.get("connection", {}).get("browse_namespace", -1)
        return await self.client.browse(node_id=path or "i=84", namespace_filter=ns)

    async def _reconnect_loop(self):
        while not self.client.is_connected:
            await self.client.reconnect()
            if self.client.is_connected:
                self._task = asyncio.create_task(self._poll_loop())
                return
            await asyncio.sleep(10)

    async def _poll_loop(self):
        self._running = True
        while self._running:
            try:
                raw = await self.client.read_values(self.mapper.node_ids)
                if raw:
                    readings = self.mapper.map_values(raw)
                    self._last_success = datetime.now(timezone.utc)
                await asyncio.sleep(self._interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self._last_error = str(e)
                self._last_error_at = datetime.now(timezone.utc)
                logger.warning("OPC UA poll error: %s", e)
                await asyncio.sleep(self._interval)
        self._running = False
