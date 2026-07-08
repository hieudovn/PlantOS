"""Modbus RTU Connector — implements BaseConnector for Modbus RTU (serial)."""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any

from agent.connectors.base import (
    BaseConnector, ConnectorStatus, RawReading, TagConfig, TestResult,
)
from agent.connectors.modbus.rtu_client import ModbusRtuClient
from agent.connectors.modbus.mapper import ModbusMapper

logger = logging.getLogger(__name__)


class ModbusRtuConnector(BaseConnector):
    """Modbus RTU connector — polls holding registers over serial port.

    Same register mapping as Modbus TCP (holding, coil) with float32/int32/uint32 decode.
    Serial port config: port, baudrate, parity, stopbits, bytesize.
    """

    def __init__(self, connector_id: str, config: dict):
        super().__init__(connector_id, config)
        self.connector_type = "modbus_rtu"
        conn = config.get("connection", {})
        self.client = ModbusRtuClient(
            port=conn.get("port", "COM3" if __import__("sys").platform == "win32" else "/dev/ttyUSB0"),
            baudrate=conn.get("baudrate", 9600),
            parity=conn.get("parity", "N"),
            stopbits=conn.get("stopbits", 1),
            bytesize=conn.get("bytesize", 8),
            unit_id=conn.get("unit_id", 1),
            timeout=conn.get("timeout", 3.0),
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
        if not conn.get("port"):
            errors.append("Missing 'connection.port' (e.g. /dev/ttyUSB0 or COM3)")
        baud = conn.get("baudrate", 9600)
        if baud not in (9600, 19200, 38400, 115200):
            errors.append(f"Unsupported baudrate: {baud}. Use 9600, 19200, 38400, or 115200")
        return errors

    async def test_connection(self) -> TestResult:
        import time
        conn = self.config.get("connection", {})
        test_client = ModbusRtuClient(
            port=conn.get("port", "/dev/ttyUSB0"),
            baudrate=conn.get("baudrate", 9600),
            parity=conn.get("parity", "N"),
            stopbits=conn.get("stopbits", 1),
            bytesize=conn.get("bytesize", 8),
            unit_id=conn.get("unit_id", 1),
            timeout=conn.get("timeout", 3.0),
        )
        start = time.monotonic()
        ok = test_client.connect()
        elapsed = (time.monotonic() - start) * 1000
        if ok:
            # Try reading a known register to verify communication
            regs = test_client.read_holding_registers(0, 2)
            test_client.disconnect()
            if regs is not None:
                return TestResult(success=True, message="Modbus RTU device reachable",
                                  latency_ms=round(elapsed, 1))
            return TestResult(success=False, message="Connected but register read failed",
                              latency_ms=round(elapsed, 1))
        return TestResult(success=False, message="Modbus RTU connection failed",
                          detail=f"Could not open {conn.get('port', '/dev/ttyUSB0')}",
                          latency_ms=round(elapsed, 1))

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
                max_addr = max(addrs) + 2
                count = max_addr - min_addr
                regs = await loop.run_in_executor(
                    None, self.client.read_holding_registers, min_addr, count
                )
                if regs:
                    raw_values: dict[int, Any] = {}
                    all_readings.extend(mapper.map_holding_registers(regs, min_addr, raw_values))
        return all_readings

    async def browse(self, path: str = "") -> list[dict[str, Any]]:
        return [
            {"node_id": "0-99", "name": "Holding Registers 0-99", "has_children": False, "depth": 0},
            {"node_id": "100-199", "name": "Holding Registers 100-199", "has_children": False, "depth": 0},
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
                if all_readings:
                    self._last_success = datetime.now(timezone.utc)
                await asyncio.sleep(self._interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self._last_error = str(e)
                self._last_error_at = datetime.now(timezone.utc)
                logger.warning("Modbus RTU poll error: %s", e)
                await asyncio.sleep(self._interval)
        self._running = False
