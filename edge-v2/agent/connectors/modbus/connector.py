"""Modbus TCP Connector — implements BaseConnector for Modbus TCP protocol."""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any

from agent.connectors.base import (
    BaseConnector, ConnectorStatus, RawReading, TagConfig, TestResult,
)
from agent.connectors.modbus.client import ModbusClient
from agent.connectors.modbus.mapper import ModbusMapper

logger = logging.getLogger(__name__)


class ModbusTcpConnector(BaseConnector):
    """Modbus TCP connector — polls holding registers, returns RawReadings.

    Refactored from edge/agent/collectors/modbus/ into BaseConnector interface.
    Supports Float32, Int32, UInt32 decode via paired registers.
    """

    def __init__(self, connector_id: str, config: dict):
        super().__init__(connector_id, config)
        self.connector_type = "modbus_tcp"
        conn = config.get("connection", {})
        self.client = ModbusClient(
            host=conn.get("host", "127.0.0.1"),
            port=conn.get("port", 502),
            unit_id=conn.get("unit_id", 1),
            timeout=conn.get("timeout", 5.0),
        )
        tags_raw = config.get("tags", [])
        self.tags = [TagConfig(**t) if isinstance(t, dict) else t for t in tags_raw]
        self.mapper = ModbusMapper(self.tags)
        self._interval = config.get("poll_interval_ms", 1000) / 1000
        self._task: asyncio.Task | None = None
        self._last_success: datetime | None = None
        self._last_error: str | None = None
        self._last_error_at: datetime | None = None

    async def validate_config(self, config: dict) -> list[str]:
        errors = []
        conn = config.get("connection", {})
        if not conn.get("host"):
            errors.append("Missing 'connection.host'")
        return errors

    async def test_connection(self) -> TestResult:
        import time
        conn = self.config.get("connection", {})
        test_client = ModbusClient(
            host=conn.get("host", "127.0.0.1"),
            port=conn.get("port", 502),
            unit_id=conn.get("unit_id", 1),
            timeout=conn.get("timeout", 5.0),
        )
        start = time.monotonic()
        ok = test_client.connect()
        elapsed = (time.monotonic() - start) * 1000
        if ok:
            test_client.disconnect()
            return TestResult(success=True, message="Modbus TCP server reachable",
                              latency_ms=round(elapsed, 1))
        return TestResult(success=False, message="Modbus TCP connection failed",
                          detail="Could not connect to endpoint", latency_ms=round(elapsed, 1))

    async def start(self):
        loop = asyncio.get_event_loop()
        ok = await loop.run_in_executor(None, self.client.connect)
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
        self.client.disconnect()
        self._running = False

    async def status(self) -> ConnectorStatus:
        return ConnectorStatus(
            connector_id=self.connector_id,
            type=self.connector_type,
            status="running" if self._running else "stopped",
            connected=self.client.is_connected(),
            signal_count=len(self.tags),
            last_success_at=self._last_success,
            last_error=self._last_error,
            last_error_at=self._last_error_at,
        )

    async def read_tags(self, tag_configs: list[TagConfig]) -> list[RawReading]:
        loop = asyncio.get_event_loop()
        mapper = ModbusMapper(tag_configs)
        all_readings = []

        if mapper.holding_tags:
            addrs = mapper.get_holding_registers()
            if addrs:
                min_addr = min(addrs)
                max_addr = max(addrs) + 2  # +2 for float32 pairs
                count = max_addr - min_addr
                regs = await loop.run_in_executor(
                    None, self.client.read_holding_registers, min_addr, count
                )
                if regs:
                    raw_values: dict[int, Any] = {}
                    all_readings.extend(
                        mapper.map_holding_registers(regs, min_addr, raw_values)
                    )

        return all_readings

    async def browse(self, path: str = "") -> list[dict[str, Any]]:
        # Modbus has no browse — return suggested register ranges
        return [
            {"node_id": "0-99", "name": "Holding Registers 0-99", "has_children": False, "depth": 0},
            {"node_id": "100-199", "name": "Holding Registers 100-199", "has_children": False, "depth": 0},
            {"node_id": "200-299", "name": "Holding Registers 200-299", "has_children": False, "depth": 0},
        ]

    async def _reconnect_loop(self):
        delay = 1.0
        while not self.client.is_connected():
            await asyncio.sleep(delay)
            loop = asyncio.get_event_loop()
            ok = await loop.run_in_executor(None, self.client.connect)
            if ok:
                self._task = asyncio.create_task(self._poll_loop())
                return
            delay = min(delay * 2, 30.0)

    async def _poll_loop(self):
        self._running = True
        while self._running:
            try:
                loop = asyncio.get_event_loop()
                all_readings = []

                # Read holding registers in batch
                if self.mapper.holding_tags:
                    addrs = self.mapper.get_holding_registers()
                    if addrs:
                        min_addr = min(addrs)
                        max_addr = max(addrs) + 2
                        count = max_addr - min_addr
                        regs = await loop.run_in_executor(
                            None, self.client.read_holding_registers, min_addr, count
                        )
                        if regs:
                            raw_values: dict[int, Any] = {}
                            all_readings.extend(
                                self.mapper.map_holding_registers(regs, min_addr, raw_values)
                            )

                # Read coils in batch
                if self.mapper.coil_tags:
                    coil_addrs = sorted([int(t.source_ref) for t in self.mapper.coil_tags])
                    if coil_addrs:
                        min_c = min(coil_addrs)
                        count_c = max(coil_addrs) - min_c + 1
                        bits = await loop.run_in_executor(
                            None, self.client.read_coils, min_c, count_c
                        )
                        if bits:
                            all_readings.extend(self.mapper.map_coils(bits, min_c))

                if all_readings:
                    self._last_success = datetime.now(timezone.utc)
                    # TODO: feed to processing pipeline (E2V2-3)

                await asyncio.sleep(self._interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self._last_error = str(e)
                self._last_error_at = datetime.now(timezone.utc)
                logger.warning("Modbus poll error: %s", e)
                await asyncio.sleep(self._interval)
        self._running = False
