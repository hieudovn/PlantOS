"""Modbus RTU client wrapper — serial port connection, register reads."""

import logging
import struct
from typing import Any

logger = logging.getLogger(__name__)

try:
    from pymodbus.client import ModbusSerialClient as PyModbusSerialClient
    from pymodbus.exceptions import ModbusException
    HAS_MODBUS_RTU = True
except ImportError:
    HAS_MODBUS_RTU = False


class ModbusRtuClient:
    """Wraps pymodbus serial client for Modbus RTU over RS-485/RS-232."""

    def __init__(self, port: str = "/dev/ttyUSB0", baudrate: int = 9600,
                 parity: str = "N", stopbits: int = 1, bytesize: int = 8,
                 unit_id: int = 1, timeout: float = 3.0):
        self.port = port
        self.baudrate = baudrate
        self.parity = parity.upper()[0] if parity else "N"
        self.stopbits = stopbits
        self.bytesize = bytesize
        self.unit_id = unit_id
        self.timeout = timeout
        self._client: PyModbusSerialClient | None = None

    def connect(self) -> bool:
        if not HAS_MODBUS_RTU:
            logger.warning("pymodbus not installed — Modbus RTU unavailable")
            return False
        try:
            self._client = PyModbusSerialClient(
                port=self.port,
                baudrate=self.baudrate,
                parity=self.parity,
                stopbits=self.stopbits,
                bytesize=self.bytesize,
                timeout=self.timeout,
            )
            return self._client.connect()
        except Exception as e:
            logger.warning("Modbus RTU connect failed on %s: %s", self.port, e)
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
        if not self._client or not self.is_connected():
            return None
        try:
            result = self._client.read_holding_registers(address, count, slave=self.unit_id)
            if result and not result.isError():
                return result.registers
            logger.warning("Modbus RTU read error at %d count %d", address, count)
            return None
        except ModbusException as e:
            logger.warning("Modbus RTU read exception: %s", e)
            return None

    def read_coils(self, address: int, count: int) -> list[bool] | None:
        if not self._client or not self.is_connected():
            return None
        try:
            result = self._client.read_coils(address, count, slave=self.unit_id)
            if result and not result.isError():
                return result.bits
            return None
        except ModbusException as e:
            logger.warning("Modbus RTU coil read error: %s", e)
            return None

    @staticmethod
    def decode_float32(registers: list[int]) -> float:
        if len(registers) < 2:
            return 0.0
        raw = struct.pack(">HH", registers[0], registers[1])
        return struct.unpack(">f", raw)[0]

    @staticmethod
    def decode_uint32(registers: list[int]) -> int:
        if len(registers) < 2:
            return 0
        raw = struct.pack(">HH", registers[0], registers[1])
        return struct.unpack(">I", raw)[0]
