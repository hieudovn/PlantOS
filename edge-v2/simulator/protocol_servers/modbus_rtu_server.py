"""Modbus RTU Simulator — serves test data via pymodbus serial server.

Uses a virtual serial pair for testing without physical hardware.
On Linux: uses ptty. On Windows: uses COM port loopback.

Usage:
    python -m edge_v2.simulator.protocol_servers.modbus_rtu_server
"""

import logging

logger = logging.getLogger(__name__)

try:
    from pymodbus.server import StartSerialServer
    from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext
    from pymodbus.datastore.store import ModbusSequentialDataBlock
    from pymodbus.device import ModbusDeviceIdentification
    HAS_MODBUS = True
except ImportError:
    HAS_MODBUS = False


def create_server_context() -> ModbusServerContext:
    """Create a Modbus data store with test values.

    Holding registers:
        0:    12345  (test_flow_rate)
        1-2:  165.5 as float32 (test_pressure)
        3:    789    (test_level)
        4-5:  42.5 as float32 (test_temperature)
        6-9:  0     (unused)
    """
    import struct

    # Pre-populate registers with test values
    registers = [0] * 100
    registers[0] = 12345  # flow_rate (int)

    # pressure = 165.5 as float32 in registers 1-2
    pressure_bytes = struct.pack(">f", 165.5)
    registers[1], registers[2] = struct.unpack(">HH", pressure_bytes)

    registers[3] = 789  # level (int)

    # temperature = 42.5 as float32 in registers 4-5
    temp_bytes = struct.pack(">f", 42.5)
    registers[4], registers[5] = struct.unpack(">HH", temp_bytes)

    store = ModbusSlaveContext(
        di=ModbusSequentialDataBlock(0, [0] * 100),
        co=ModbusSequentialDataBlock(0, [False] * 100),
        hr=ModbusSequentialDataBlock(0, registers),
        ir=ModbusSequentialDataBlock(0, [0] * 100),
    )
    return ModbusServerContext(slaves=store, single=True)


def run_server(port: str = "/dev/ptyp0", baudrate: int = 9600):
    """Run the Modbus RTU simulator server."""
    if not HAS_MODBUS:
        logger.warning("pymodbus not installed — cannot start Modbus RTU simulator")
        return

    context = create_server_context()

    # Device identification
    identity = ModbusDeviceIdentification()
    identity.VendorName = "PlantOS"
    identity.ProductCode = "EDGE-V2-SIM"
    identity.VendorUrl = "https://plantos.io"
    identity.ProductName = "Edge v2 Modbus RTU Simulator"
    identity.ModelName = "EDGEV2-MODBUS-RTU-SIM"

    logger.info("Starting Modbus RTU simulator on %s (baud=%d)", port, baudrate)

    StartSerialServer(
        context=context,
        identity=identity,
        port=port,
        baudrate=baudrate,
        stopbits=1,
        bytesize=8,
        parity="N",
        timeout=1.0,
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_server()
