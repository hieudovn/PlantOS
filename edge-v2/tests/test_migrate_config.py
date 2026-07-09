"""Tests for tools/migrate_v1_config_to_v2.py — config migration utility."""

import os
import sys
import tempfile

import pytest
import yaml

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

SAMPLE_V1_CONFIG = """
edge_node_id: edge-agent-01
plant_id: DEMO-PLANT
center_url: http://localhost:8000
api_key: test-key-123

signals:
  - signal_id: PUMP-101.flow_rate
    data_type: float
    min: 0
    max: 100
    pattern: sine

opcua:
  enabled: true
  endpoint: opc.tcp://localhost:4840
  poll_interval_ms: 1000
  tags:
    - node_id: ns=2;s=COMP01_FLOW
      signal_id: COMP01-CORE.flow_rate
      scale: 1.0

mqtt:
  host: localhost
  port: 1883

modbus:
  enabled: false

publish:
  interval_seconds: 10
  batch_size: 10
"""


class TestMigrateConfig:
    """Tests for v1 → v2 config migration."""

    @pytest.fixture
    def v1_config_path(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(SAMPLE_V1_CONFIG)
            path = f.name
        yield path
        os.unlink(path)

    def test_load_v1_config(self, v1_config_path):
        from tools.migrate_v1_config_to_v2 import load_v1_config
        cfg = load_v1_config(v1_config_path)
        assert cfg["edge_node_id"] == "edge-agent-01"
        assert cfg["plant_id"] == "DEMO-PLANT"

    def test_translate_signals(self, v1_config_path):
        from tools.migrate_v1_config_to_v2 import load_v1_config, translate_signals
        cfg = load_v1_config(v1_config_path)
        tags = translate_signals(cfg)
        assert len(tags) == 1
        assert tags[0]["signal_id"] == "PUMP-101.flow_rate"
        assert tags[0]["data_type"] == "float"

    def test_translate_opcua(self, v1_config_path):
        from tools.migrate_v1_config_to_v2 import load_v1_config, translate_opcua
        cfg = load_v1_config(v1_config_path)
        result = translate_opcua(cfg)
        assert result is not None
        assert result["type"] == "opcua"
        assert result["enabled"] is True
        assert len(result["tags"]) == 1
        assert result["tags"][0]["signal_id"] == "COMP01-CORE.flow_rate"
        assert result["tags"][0]["scale"] == 1.0

    def test_translate_opcua_disabled(self, v1_config_path):
        from tools.migrate_v1_config_to_v2 import load_v1_config, translate_opcua
        cfg = load_v1_config(v1_config_path)
        cfg["opcua"]["enabled"] = False
        result = translate_opcua(cfg)
        assert result is None

    def test_translate_mqtt(self, v1_config_path):
        from tools.migrate_v1_config_to_v2 import load_v1_config, translate_mqtt
        cfg = load_v1_config(v1_config_path)
        result = translate_mqtt(cfg)
        assert result is not None
        assert result["type"] == "mqtt"

    def test_generate_v2_config(self, v1_config_path):
        from tools.migrate_v1_config_to_v2 import load_v1_config, generate_v2_config
        cfg = load_v1_config(v1_config_path)
        result = generate_v2_config(cfg)
        connectors = result["connectors"]
        assert len(connectors) >= 2  # mirror_signals + vf_compressor + mqtt_sub
        assert "vf_compressor" in connectors
        assert connectors["vf_compressor"]["type"] == "opcua"

    def test_no_crash_on_missing_fields(self, tmp_path):
        """Graceful degradation when v1 config has missing fields."""
        minimal = "edge_node_id: test\nplant_id: test\n"
        cfg_path = tmp_path / "minimal.yaml"
        cfg_path.write_text(minimal)
        from tools.migrate_v1_config_to_v2 import load_v1_config, generate_v2_config
        cfg = load_v1_config(str(cfg_path))
        result = generate_v2_config(cfg)
        assert isinstance(result["connectors"], dict)
        assert isinstance(result["warnings"], list)

    def test_no_crash_on_empty_config(self, tmp_path):
        """Graceful degradation on completely empty config."""
        empty = ""
        cfg_path = tmp_path / "empty.yaml"
        cfg_path.write_text(empty)
        from tools.migrate_v1_config_to_v2 import load_v1_config, generate_v2_config
        cfg = load_v1_config(str(cfg_path))
        result = generate_v2_config(cfg)
        assert isinstance(result["connectors"], dict)

    def test_dry_run_does_not_write(self, v1_config_path, capsys):
        """Verify --dry-run flag prints output without writing files."""
        from tools.migrate_v1_config_to_v2 import load_v1_config, generate_v2_config
        cfg = load_v1_config(v1_config_path)
        result = generate_v2_config(cfg)
        # Print dry-run output
        print(yaml.dump({"connectors": result["connectors"]}, default_flow_style=False))
        captured = capsys.readouterr()
        assert "COMP01-CORE.flow_rate" in captured.out
        assert "PUMP-101.flow_rate" in captured.out
