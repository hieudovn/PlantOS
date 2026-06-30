"""Modbus collector — poll registers, normalize, write to DuckDB."""

import asyncio
import logging
from datetime import datetime, timezone

from .client import ModbusClient
from .mapper import TagMapper

logger = logging.getLogger(__name__)


class ModbusCollector:
    def __init__(self, config: dict, buffer):
        self.config = config
        self.buffer = buffer
        self.client = ModbusClient(
            host=config.get("host", "127.0.0.1"),
            port=config.get("port", 502),
            unit_id=config.get("unit_id", 1),
        )
        self.mapper = TagMapper(config.get("tags", []))
        self.interval = config.get("poll_interval_ms", 1000) / 1000
        self._enabled = config.get("enabled", False)

    @property
    def connected(self) -> bool:
        return self.client.is_connected()

    async def start(self):
        if not self._enabled:
            logger.info("Modbus collector disabled")
            return

        if not self.client.connect():
            logger.warning("Modbus collector: connection failed, retrying...")
            # Retry in background
            asyncio.create_task(self._retry_connect())
            return

        logger.info(f"Modbus collector started ({len(self.mapper.tags)} tags)")
        asyncio.create_task(self._poll_loop())

    async def _retry_connect(self):
        while not self.client.is_connected():
            await asyncio.sleep(10)
            self.client.connect()

    async def _poll_loop(self):
        while self.client.is_connected():
            try:
                measurements = []

                # Read holding registers in batch
                if self.mapper.holding_tags:
                    addrs = self.mapper.get_holding_registers()
                    min_addr = min(addrs)
                    max_addr = max(addrs) + 1  # +1 extra for float32 pairs
                    regs = self.client.read_holding_registers(min_addr, max_addr - min_addr)
                    if regs:
                        measurements.extend(self.mapper.map_holding_values(regs, min_addr))

                # Read coils in batch
                if self.mapper.coil_tags:
                    addrs = self.mapper.get_coil_addresses()
                    min_addr = min(addrs)
                    max_addr = max(addrs) + 1
                    bits = self.client.read_coils(min_addr, max_addr - min_addr)
                    if bits:
                        measurements.extend(self.mapper.map_coil_values(bits, min_addr))

                # Write to local buffer
                if measurements:
                    now = datetime.now(timezone.utc)
                    rows = [
                        {
                            "timestamp": now.isoformat(),
                            "signal_id": m["signal_id"],
                            "value": m["value"],
                            "quality": "GOOD",
                            "source": "modbus",
                        }
                        for m in measurements
                    ]
                    self.buffer.write(rows)

            except Exception as e:
                logger.error(f"Modbus poll error: {e}")

            await asyncio.sleep(self.interval)

    async def stop(self):
        self.client.disconnect()
