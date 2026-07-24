"""Tests for BaseConnector interface, data classes, and safe apply flow."""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime, timezone


class TestDataClasses:
    """Verify data class creation and defaults."""

    def test_raw_reading_defaults(self):
        from agent.connectors.base import RawReading
        r = RawReading(source_ref="ns=2;s=Pump101", signal_id="PUMP-101.flow",
                       raw_value=12.5, timestamp=datetime.now(timezone.utc))
        assert r.source_ref == "ns=2;s=Pump101"
        assert r.signal_id == "PUMP-101.flow"
        assert r.raw_value == 12.5
        assert r.quality_hint == "GOOD"

    def test_tag_config_defaults(self):
        from agent.connectors.base import TagConfig
        t = TagConfig(tag_id="t1", source_ref="100", signal_id="PUMP-101.flow")
        assert t.data_type == "float"
        assert t.scale == 1.0
        assert t.offset == 0.0
        assert t.enabled is True

    def test_connector_status_defaults(self):
        from agent.connectors.base import ConnectorStatus
        s = ConnectorStatus(connector_id="opcua_01", type="opcua")
        assert s.status == "stopped"
        assert s.connected is False
        assert s.signal_count == 0

    def test_test_result(self):
        from agent.connectors.base import TestResult
        r = TestResult(success=True, message="Connected", latency_ms=12.5)
        assert r.success is True
        assert r.latency_ms == 12.5


class TestConnectorRegistry:
    """Verify registry lifecycle management."""

    @pytest.fixture
    def config(self):
        cfg = MagicMock()
        cfg.get.return_value = {}
        cfg._data = {}
        cfg._save = MagicMock()
        return cfg

    @pytest.fixture
    def registry(self, config):
        from agent.connectors.registry import ConnectorRegistry
        return ConnectorRegistry(config)

    def test_empty_registry(self, registry):
        assert registry.active_count == 0
        assert registry.all_ids == []

    def test_register_connector_type(self, config):
        from agent.connectors.registry import register_connector_type, CONNECTOR_REGISTRY
        from agent.connectors.opcua.connector import OpcUaConnector
        register_connector_type("opcua", OpcUaConnector)
        assert "opcua" in CONNECTOR_REGISTRY
        assert CONNECTOR_REGISTRY["opcua"] == OpcUaConnector

    def test_get_status_all_empty(self, registry):
        import asyncio
        statuses = asyncio.run(registry.get_status_all())
        assert statuses == []

    def test_list_status_sync_empty(self, registry):
        assert registry.list_status_sync() == []


class TestSafeApply:
    """Verify ConfigManager safe apply flow."""

    @pytest.fixture
    def config(self, tmp_path):
        from agent.config import ConfigManager
        cfg_path = tmp_path / "test_config.yaml"
        cfg_path.write_text("edge_node_id: TEST\nplant_id: TEST\n")
        return ConfigManager(str(cfg_path))

    def test_save_and_get_draft(self, config):
        draft = {"type": "opcua", "connection": {"endpoint": "opc.tcp://test:4840"}, "tags": []}
        version = config.save_draft("test01", draft)
        assert version == 1
        retrieved = config.get_draft("test01")
        assert retrieved["type"] == "opcua"
        assert retrieved["connection"]["endpoint"] == "opc.tcp://test:4840"

    def test_draft_version_increments(self, config):
        config.save_draft("test01", {"type": "opcua"})
        config.save_draft("test01", {"type": "modbus_tcp"})
        retrieved = config.get_draft("test01")
        assert retrieved["type"] == "modbus_tcp"

    def test_list_drafts(self, config):
        config.save_draft("test01", {"type": "opcua", "v": 1})
        config.save_draft("test01", {"type": "modbus_tcp", "v": 2})
        drafts = config.list_drafts("test01")
        assert len(drafts) == 2
        assert drafts[0]["v"] == 1
        assert drafts[1]["v"] == 2

    def test_get_draft_not_found(self, config):
        assert config.get_draft("nonexistent") is None

    def test_validate_draft_missing_fields(self, config):
        config.save_draft("test01", {"name": "test"})
        errors = config.validate_draft("test01")
        assert "Missing 'type' field" in errors
        assert "Missing 'connection' section" in errors

    def test_validate_draft_no_draft(self, config):
        errors = config.validate_draft("nonexistent")
        assert "No draft found" in errors

    def test_apply_and_confirm(self, config):
        config.save_draft("test01", {"type": "opcua", "connection": {}, "tags": []})
        backup_key = config.apply_draft("test01")
        assert backup_key is not None
        assert "test01" in str(backup_key)

        # Confirm success
        config.confirm_apply("test01", success=True)
        # Config should still be applied
        assert config.get("connectors.test01.type") == "opcua"

    def test_apply_and_rollback(self, config):
        # First save active config
        config._data.setdefault("connectors", {})["test01"] = {"type": "modbus_tcp", "connection": {}, "tags": []}
        config._save()

        # Create draft with different type
        config.save_draft("test01", {"type": "opcua", "connection": {}, "tags": []})
        config.apply_draft("test01")

        # Confirm failure triggers rollback
        config.confirm_apply("test01", success=False)
        # Config should be rolled back to modbus_tcp
        assert config._data.get("connectors", {}).get("test01", {}).get("type") == "modbus_tcp"

    def test_explicit_rollback(self, config):
        config._data.setdefault("connectors", {})["test01"] = {"type": "original", "tags": []}
        config._save()
        config.save_draft("test01", {"type": "new_type", "tags": []})
        config.apply_draft("test01")
        config.rollback("test01")
        assert config._data.get("connectors", {}).get("test01", {}).get("type") == "original"

    def test_sanitized_export(self, config):
        config._data["api_key"] = "super-secret-123"
        safe = config.export_sanitized()
        assert safe["api_key"] == "***"


class TestBaseConnector:
    """Verify BaseConnector interface contract."""

    def test_cannot_instantiate_base(self):
        from agent.connectors.base import BaseConnector
        with pytest.raises(TypeError):
            BaseConnector("test", {})  # Abstract methods not implemented

    def test_opcua_connector_implements_interface(self):
        from agent.connectors.opcua.connector import OpcUaConnector
        from agent.connectors.base import BaseConnector
        assert issubclass(OpcUaConnector, BaseConnector)

    def test_modbus_connector_implements_interface(self):
        from agent.connectors.modbus.connector import ModbusTcpConnector
        from agent.connectors.base import BaseConnector
        assert issubclass(ModbusTcpConnector, BaseConnector)

    def test_mqtt_connector_implements_interface(self):
        from agent.connectors.mqtt.connector import MqttSubscribeConnector
        from agent.connectors.base import BaseConnector
        assert issubclass(MqttSubscribeConnector, BaseConnector)

    @pytest.mark.asyncio
    async def test_opcua_validate_config(self):
        from agent.connectors.opcua.connector import OpcUaConnector
        c = OpcUaConnector("test", {"connection": {"endpoint": "opc.tcp://test:4840"}})
        errors = await c.validate_config({"connection": {"endpoint": "opc.tcp://test:4840"}})
        assert len(errors) == 0

    @pytest.mark.asyncio
    async def test_opcua_validate_config_missing_endpoint(self):
        from agent.connectors.opcua.connector import OpcUaConnector
        c = OpcUaConnector("test", {"connection": {}})
        errors = await c.validate_config({"connection": {}})
        assert len(errors) > 0
        assert any("endpoint" in e for e in errors)

    @pytest.mark.asyncio
    async def test_modbus_validate_config(self):
        from agent.connectors.modbus.connector import ModbusTcpConnector
        c = ModbusTcpConnector("test", {"connection": {"host": "192.168.1.10"}})
        errors = await c.validate_config({"connection": {"host": "192.168.1.10"}})
        assert len(errors) == 0

    @pytest.mark.asyncio
    async def test_modbus_validate_config_missing_host(self):
        from agent.connectors.modbus.connector import ModbusTcpConnector
        c = ModbusTcpConnector("test", {"connection": {}})
        errors = await c.validate_config({"connection": {}})
        assert len(errors) > 0
        assert any("host" in e for e in errors)

    @pytest.mark.asyncio
    async def test_mqtt_validate_config(self):
        from agent.connectors.mqtt.connector import MqttSubscribeConnector
        c = MqttSubscribeConnector("test", {"connection": {"host": "localhost"}, "tags": [{"tag_id": "t1", "source_ref": "topic/test", "signal_id": "sig-1"}]})
        errors = await c.validate_config({"connection": {"host": "localhost"}, "tags": [{"tag_id": "t1", "source_ref": "topic/test", "signal_id": "sig-1"}]})
        assert len(errors) == 0

    def test_opcua_connector_type(self):
        from agent.connectors.opcua.connector import OpcUaConnector
        c = OpcUaConnector("test", {"connection": {}})
        assert c.connector_type == "opcua"

    def test_modbus_connector_type(self):
        from agent.connectors.modbus.connector import ModbusTcpConnector
        c = ModbusTcpConnector("test", {"connection": {}})
        assert c.connector_type == "modbus_tcp"

    def test_mqtt_connector_type(self):
        from agent.connectors.mqtt.connector import MqttSubscribeConnector
        c = MqttSubscribeConnector("test", {"connection": {}})
        assert c.connector_type == "mqtt"
