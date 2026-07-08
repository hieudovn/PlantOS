"""Modbus tag mapper — register address → signal_id for RawReading generation."""

from datetime import datetime, timezone
from typing import Any

from agent.connectors.base import RawReading, TagConfig
from agent.connectors.modbus.client import ModbusClient


class ModbusMapper:
    """Maps Modbus register reads to RawReadings."""

    def __init__(self, tags: list[TagConfig]):
        self.tags = tags
        self.holding_tags = [t for t in tags if t.enabled and "holding" in t.data_type]
        self.coil_tags = [t for t in tags if t.enabled and "coil" in t.data_type]

    def get_holding_registers(self) -> list[int]:
        """Get all holding register addresses."""
        addrs = []
        for t in self.holding_tags:
            try:
                addrs.append(int(t.source_ref))
            except ValueError:
                pass
        return sorted(addrs)

    def map_holding_registers(self, registers: list[int], start_addr: int,
                               raw_values: dict[int, Any]) -> list[RawReading]:
        """Map raw register values to RawReadings."""
        readings = []
        now = datetime.now(timezone.utc)
        for i, reg_val in enumerate(registers):
            addr = start_addr + i
            raw_values[addr] = reg_val

        for t in self.holding_tags:
            try:
                addr = int(t.source_ref)
            except ValueError:
                continue
            if addr not in raw_values:
                continue

            value = float(raw_values[addr])
            # Float32 decode for paired registers
            if t.data_type == "float32_holding":
                if addr + 1 in raw_values:
                    value = float(ModbusClient.decode_float32([raw_values[addr], raw_values[addr + 1]]))
                else:
                    continue
            elif t.data_type == "uint32_holding":
                if addr + 1 in raw_values:
                    value = float(ModbusClient.decode_uint32([raw_values[addr], raw_values[addr + 1]]))
                else:
                    continue

            # Scale + offset (raw mapping)
            if t.scale != 1.0 or t.offset != 0.0:
                value = value * t.scale + t.offset

            readings.append(RawReading(
                source_ref=str(addr),
                signal_id=t.signal_id,
                raw_value=value,
                timestamp=now,
            ))
        return readings

    def map_coils(self, coil_bits: list[bool], start_addr: int) -> list[RawReading]:
        """Map coil bits to RawReadings."""
        readings = []
        now = datetime.now(timezone.utc)
        for i, bit in enumerate(coil_bits):
            addr = start_addr + i
            for t in self.coil_tags:
                try:
                    if int(t.source_ref) == addr:
                        readings.append(RawReading(
                            source_ref=str(addr),
                            signal_id=t.signal_id,
                            raw_value=1.0 if bit else 0.0,
                            timestamp=now,
                        ))
                except ValueError:
                    continue
        return readings
