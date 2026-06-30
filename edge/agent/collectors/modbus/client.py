"""Modbus TCP client wrapper."""

import logging
from pymodbus.client import ModbusTcpClient

logger = logging.getLogger(__name__)


class ModbusClient:
    def __init__(self, host: str = "127.0.0.1", port: int = 502, unit_id: int = 1):
        self.host = host
        self.port = port
        self.unit_id = unit_id
        self.client = ModbusTcpClient(host, port)
        self._connected = False

    def connect(self) -> bool:
        try:
            self._connected = self.client.connect()
            if self._connected:
                logger.info(f"Modbus connected: {self.host}:{self.port}")
            return self._connected
        except Exception as e:
            logger.warning(f"Modbus connect failed: {e}")
            return False

    def disconnect(self):
        self.client.close()
        self._connected = False

    def is_connected(self) -> bool:
        return self._connected

    def read_holding_registers(self, address: int, count: int = 1):
        if not self._connected:
            return None
        result = self.client.read_holding_registers(address, count, slave=self.unit_id)
        if result.isError():
            logger.warning(f"Modbus read error at {address}")
            return None
        return result.registers

    def read_coils(self, address: int, count: int = 1):
        if not self._connected:
            return None
        result = self.client.read_coils(address, count, slave=self.unit_id)
        if result.isError():
            return None
        return result.bits
