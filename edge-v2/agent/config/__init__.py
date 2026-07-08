"""Config Manager — loads, validates, and manages config ownership."""

import yaml
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class ConfigManager:
    """Loads, validates, saves, versions, and manages config ownership.

    Stub for E2V2-0. Full ownership model, draft/active/applied lifecycle,
    and conflict resolution added in later phases.
    """

    def __init__(self, config_path: str):
        self.config_path = Path(config_path)
        self._data: dict[str, Any] = {}
        self._load()

    def _load(self):
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config not found: {self.config_path}")
        with open(self.config_path) as f:
            self._data = yaml.safe_load(f) or {}

    @property
    def edge_node_id(self) -> str:
        return self._data.get("edge_node_id", "EDGEV2-PC-01")

    @property
    def plant_id(self) -> str:
        return self._data.get("plant_id", "EDGEV2-DEMO")

    @property
    def center_url(self) -> str:
        return self._data.get("center_url", "http://localhost:8000")

    @property
    def api_key(self) -> str:
        return self._data.get("api_key", "")

    @property
    def db_path(self) -> str:
        return self._data.get("buffer", {}).get("path", "edge-v2/data/edge_data.duckdb")

    @property
    def buffer_retention_days(self) -> int:
        return self._data.get("buffer", {}).get("retention_days", 7)

    @property
    def mqtt_host(self) -> str:
        return self._data.get("mqtt", {}).get("host", "localhost")

    @property
    def mqtt_port(self) -> int:
        return self._data.get("mqtt", {}).get("port", 1883)

    @property
    def mqtt_topic_prefix(self) -> str:
        return self._data.get("mqtt", {}).get("topic_prefix", "avenue/edgev2-demo")

    @property
    def center_ingest_url(self) -> str:
        return self._data.get("http", {}).get("ingest_url",
                                              f"{self.center_url}/api/v1/measurements/ingest")

    @property
    def heartbeat_url(self) -> str:
        return self._data.get("heartbeat", {}).get("url",
                                                   f"{self.center_url}/api/v1/edge-nodes/heartbeat")

    @property
    def heartbeat_interval(self) -> int:
        return self._data.get("heartbeat", {}).get("interval_seconds", 10)

    @property
    def publish_interval(self) -> int:
        return self._data.get("publish", {}).get("interval_seconds", 10)

    @property
    def batch_size(self) -> int:
        return self._data.get("publish", {}).get("batch_size", 10)

    @property
    def web_port(self) -> int:
        return self._data.get("web", {}).get("port", 8011)

    def _save(self):
        """Persist current config back to YAML file."""
        with open(self.config_path, 'w') as f:
            yaml.dump(self._data, f, default_flow_style=False, allow_unicode=True)

    # -- Auth config (managed by LocalAuthManager) --
    @property
    def admin_hash(self) -> str | None:
        return self._data.get("auth", {}).get("admin_hash")

    def set_admin_hash(self, hashed: str):
        self._data.setdefault("auth", {})["admin_hash"] = hashed
        self._save()

    @property
    def session_secret(self) -> str:
        return self._data.get("auth", {}).get("session_secret", "plantos-edge-default-secret")

    def get(self, key: str, default: Any = None) -> Any:
        """Get a config value, supporting dot-separated nested keys."""
        parts = key.split(".")
        node = self._data
        for p in parts:
            if isinstance(node, dict):
                node = node.get(p)
            else:
                return default
        return node if node is not None else default
        if "." in key:
            parts = key.split(".")
            obj = self._data
            for part in parts:
                if isinstance(obj, dict):
                    obj = obj.get(part)
                    if obj is None:
                        return default
                else:
                    return default
            return obj
        return self._data.get(key, default)

    def _save(self):
        """Write current config back to disk."""
        import yaml as yaml_lib
        # Preserve original file if possible
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, "w") as f:
            yaml_lib.dump(self._data, f, default_flow_style=False)

    def export_sanitized(self) -> dict:
        """Export config with secrets masked."""
        safe = dict(self._data)
        if "api_key" in safe:
            safe["api_key"] = "***"
        return safe
