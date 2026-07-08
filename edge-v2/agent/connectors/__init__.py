"""Connector Registry — BaseConnector interface, registry, OPC UA / Modbus / MQTT."""

from agent.connectors.registry import ConnectorRegistry, register_connector_type, CONNECTOR_REGISTRY
from agent.connectors.opcua.connector import OpcUaConnector
from agent.connectors.modbus.connector import ModbusTcpConnector
from agent.connectors.mqtt.connector import MqttSubscribeConnector
from agent.connectors.base import BaseConnector, RawReading, ConnectorStatus, TestResult, TagConfig

# Register all connector types
register_connector_type("opcua", OpcUaConnector)
register_connector_type("modbus_tcp", ModbusTcpConnector)
register_connector_type("mqtt", MqttSubscribeConnector)

__all__ = [
    "ConnectorRegistry", "BaseConnector", "RawReading",
    "ConnectorStatus", "TestResult", "TagConfig",
    "OpcUaConnector", "ModbusTcpConnector", "MqttSubscribeConnector",
]
