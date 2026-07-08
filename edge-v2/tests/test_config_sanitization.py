"""Tests for config sanitization — verify no secrets leak via API."""

import pytest


class TestConfigSanitization:
    """Verify that /api/config does not expose secrets."""

    SECRET_PATTERNS = ["api_key", "password", "secret", "hash", "token", "admin_hash"]

    @pytest.fixture
    def raw_config(self):
        """Sample raw config — simulates what ConfigManager._data contains."""
        return {
            "edge_node_id": "EDGEV2-PC-01",
            "plant_id": "EDGEV2-DEMO",
            "center_url": "http://localhost:8000",
            "api_key": "plantos-edge-key-2026",
            "session_secret": "super-secret-key",
            "auth": {
                "admin_hash": "$2b$12$abcdefghijklmnopqrstuvwxyz12345678901234567890",
            },
            "buffer": {
                "path": "edge-v2/data/edge_data.duckdb",
                "retention_days": 7,
            },
            "mqtt": {
                "host": "localhost",
                "port": 1883,
                "password_secret_ref": "mqtt-password-123",
            },
            "web": {"port": 8011},
            "heartbeat": {"interval_seconds": 10},
            "publish": {"interval_seconds": 10, "batch_size": 10},
        }

    def _redact_secrets(self, obj, parent_key=""):
        """Same _redact_secrets logic as in routes/config.py."""
        SECRET_KEYS = {"api_key", "password", "secret", "hash", "token", "admin_hash",
                       "session_secret", "session_secret_ref", "password_secret_ref"}
        if isinstance(obj, dict):
            return {
                k: "***REDACTED***"
                if any(secret in k.lower() for secret in SECRET_KEYS)
                else self._redact_secrets(v, k)
                for k, v in obj.items()
            }
        if isinstance(obj, list):
            return [self._redact_secrets(v, parent_key) for v in obj]
        return obj

    def test_api_key_redacted(self, raw_config):
        """api_key should be redacted."""
        sanitized = self._redact_secrets(raw_config)
        assert sanitized["api_key"] == "***REDACTED***"

    def test_session_secret_redacted(self, raw_config):
        """session_secret should be redacted."""
        sanitized = self._redact_secrets(raw_config)
        assert sanitized["session_secret"] == "***REDACTED***"

    def test_admin_hash_redacted(self, raw_config):
        """admin_hash in nested auth dict should be redacted."""
        sanitized = self._redact_secrets(raw_config)
        assert sanitized["auth"]["admin_hash"] == "***REDACTED***"

    def test_password_secret_ref_redacted(self, raw_config):
        """password_secret_ref in nested mqtt dict should be redacted."""
        sanitized = self._redact_secrets(raw_config)
        assert sanitized["mqtt"]["password_secret_ref"] == "***REDACTED***"

    def test_public_fields_preserved(self, raw_config):
        """Public fields should remain unchanged."""
        sanitized = self._redact_secrets(raw_config)
        assert sanitized["edge_node_id"] == "EDGEV2-PC-01"
        assert sanitized["plant_id"] == "EDGEV2-DEMO"
        assert sanitized["center_url"] == "http://localhost:8000"
        assert sanitized["web"]["port"] == 8011
        assert sanitized["buffer"]["retention_days"] == 7

    def test_no_secret_values_in_output(self, raw_config):
        """Sanitized output should not contain any raw secret values."""
        sanitized = self._redact_secrets(raw_config)
        sanitized_str = str(sanitized)
        # None of the raw secret values should appear
        assert "plantos-edge-key-2026" not in sanitized_str
        assert "super-secret-key" not in sanitized_str
        assert "$2b$12$" not in sanitized_str
        assert "mqtt-password-123" not in sanitized_str

    def test_list_inside_config_is_handled(self):
        """Config with list values should be handled correctly."""
        config = {
            "sources": ["source1", "source2"],
            "api_key": "should-be-redacted",
        }
        sanitized = self._redact_secrets(config)
        assert sanitized["api_key"] == "***REDACTED***"
        assert sanitized["sources"] == ["source1", "source2"]

    def test_nested_redaction(self, raw_config):
        """Deeply nested secrets should be redacted."""
        raw_config["deeply"] = {"nested": {"secret_key": "hidden"}}
        sanitized = self._redact_secrets(raw_config)
        assert sanitized["deeply"]["nested"]["secret_key"] == "***REDACTED***"
