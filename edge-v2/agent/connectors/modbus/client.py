"""Modbus TCP client wrapper — handles connection, register reads."""

import logging
import struct
from typing import Any

logger = logging.getLogger(__name__)

try:
    from pymodbus.client import ModbusTcpClient as PyModbusClient
    from pymodbus.exceptions import ModbusException
    HAS_MODBUS = True
except ImportError:
    HAS_MODBUS = False


class ModbusClient:
    """Wraps pymodbus with float32 decode and batch register reads."""

    def __init__(self, host: str, port: int = 502, unit_id: int = 1, timeout: float = 5.0):
        self.host = host
        self.port = port
        self.unit_id = unit_id
        self.timeout = timeout
        self._client: PyModbusClient | None = None

    def connect(self) -> bool:
        if not HAS_MODBUS:
            logger.warning("pymodbus not installed — Modbus unavailable")
            return False
        try:
            self._client = PyModbusClient(
                host=self.host, port=self.port, timeout=self.timeout
            )
            return self._client.connect()
        except Exception as e:
            logger.warning("Modbus connect failed: %s", e)
            return False

    def is_connected(self) -> bool:
        if not self._client:
            return False
        try:
            return self._client.is_socket_open()
        except Exception:
            return False

    def disconnect(self):
        if self._client:
            try:
                self._client.close()
            except Exception:
                pass
            self._client = None

    def read_holding_registers(self, address: int, count: int) -> list[int] | None:
        """Read holding registers. Returns list of ints or None."""
        if not self._client or not self.is_connected():
            return None
        try:
            result = self._client.read_holding_registers(address, count, slave=self.unit_id)
            if result and not result.isError():
                return result.registers
            logger.warning("Modbus read error at %d count %d", address, count)
            return None
        except ModbusException as e:
            logger.warning("Modbus read exception: %s", e)
            return None

    def read_coils(self, address: int, count: int) -> list[bool] | None:
        """Read coils. Returns list of bools or None."""
        if not self._client or not self.is_connected():
            return None
        try:
            result = self._client.read_coils(address, count, slave=self.unit_id)
            if result and not result.isError():
                return result.bits
            return None
        except ModbusException as e:
            logger.warning("Modbus coil read error: %s", e)
            return None

    @staticmethod
    def decode_float32(registers: list[int]) -> float:
        """Decode two 16-bit registers to a 32-bit float."""
        if len(registers) < 2:
            return 0.0
        raw = struct.pack(">HH", registers[0], registers[1])
        return struct.unpack(">f", raw)[0]

    @staticmethod
    def decode_int32(registers: list[int]) -> int:
        """Decode two 16-bit registers to a 32-bit signed int."""
        if len(registers) < 2:
            return 0
        raw = struct.pack(">HH", registers[0], registers[1])
        return struct.unpack(">i", raw)[0]

    @staticmethod
    def decode_uint32(registers: list[int]) -> int:
        """Decode two 16-bit registers to a 32-bit unsigned int."""
        if len(registers) < 2:
            return 0
        raw = struct.pack(">HH", registers[0], registers[1])
        return struct.unpack(">I", raw)[0]
