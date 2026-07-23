"""Config Manager — loads, validates, and manages config ownership."""

import os
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
        return os.environ.get("EDGE_SESSION_SECRET",
            self._data.get("auth", {}).get("session_secret", ""))

    @property
    def center_url(self) -> str:
        return os.environ.get("CENTER_URL",
            self._data.get("center_url", "https://localhost"))

    @property
    def api_key(self) -> str:
        return os.environ.get("EDGE_API_KEY",
            self._data.get("api_key", ""))

    @property
    def center_password(self) -> str:
        return os.environ.get("EDGE_CENTER_PASSWORD",
            self._data.get("auth", {}).get("center_password", ""))

    def get(self, key: str, default: Any = None) -> Any:
        """Get a config value, supporting dot-separated nested keys."""
        if "." in key:
            parts = key.split(".")
            node = self._data
            for p in parts:
                if isinstance(node, dict):
                    node = node.get(p)
                else:
                    return default
            return node if node is not None else default
        return self._data.get(key, default)

    def _save(self):
        """Write current config back to disk."""
        import yaml as yaml_lib
        # Preserve original file if possible
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, "w") as f:
            yaml_lib.dump(self._data, f, default_flow_style=False)

    # -- Safe Apply (connector drafts) ----------------------------------------
    #
    # Canonical paths:
    #   Active:   connectors.<connector_id>
    #   Draft:    _drafts.connectors.<connector_id>.<version>
    #   Backup:   _backups.connectors.<connector_id>.<timestamp>

    def _draft_section(self, section: str) -> str:
        """Normalize section to canonical draft path."""
        if section.startswith("connectors."):
            return section
        if section.startswith("connector_"):
            # Legacy: connector_opcua_01 → connectors.opcua_01
            return section.replace("connector_", "connectors.", 1)
        return f"connectors.{section}"

    def save_draft(self, section: str, fragment: dict) -> int:
        """Save a connector draft config. Returns draft version number."""
        canon = self._draft_section(section)
        drafts = self._data.setdefault("_drafts", {})
        connectors_drafts = drafts.setdefault("connectors", {})
        conn_drafts = connectors_drafts.setdefault(canon, {})
        version = conn_drafts.get("_version", 0) + 1
        conn_drafts[f"v{version}"] = fragment
        conn_drafts["_version"] = version
        self._save()
        return version

    def get_draft(self, section: str) -> dict | None:
        """Get the latest draft for a section."""
        canon = self._draft_section(section)
        drafts = self._data.get("_drafts", {})
        connectors_drafts = drafts.get("connectors", {})
        conn_drafts = connectors_drafts.get(canon, {})
        version = conn_drafts.get("_version", 0)
        if version == 0:
            return None
        return conn_drafts.get(f"v{version}")

    def list_drafts(self, section: str) -> list[dict]:
        """List all drafts for a section."""
        canon = self._draft_section(section)
        drafts = self._data.get("_drafts", {})
        connectors_drafts = drafts.get("connectors", {})
        conn_drafts = connectors_drafts.get(canon, {})
        result = []
        i = 1
        while conn_drafts.get(f"v{i}"):
            result.append(conn_drafts[f"v{i}"])
            i += 1
        return result

    def validate_draft(self, section: str) -> list[str]:
        """Validate a connector draft. Returns list of error messages."""
        draft = self.get_draft(section)
        if not draft:
            return ["No draft found"]
        errors = []
        if "type" not in draft:
            errors.append("Missing 'type' field")
        if "connection" not in draft:
            errors.append("Missing 'connection' section")
        return errors

    def apply_draft(self, section: str) -> str | None:
        """Promote a draft to active config. Returns backup path or None."""
        draft = self.get_draft(section)
        if not draft:
            return None
        from datetime import datetime, timezone
        canon = self._draft_section(section)
        # Extract connector_id from canonical path (connectors.<id>)
        conn_id = canon.split(".", 1)[1] if "." in canon else canon
        timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
        backup_key = f"_backups.connectors.{conn_id}.{timestamp}"
        backups = self._data.setdefault("_backups", {})
        bs_conn = backups.setdefault("connectors", {})

        # Backup current active config
        connectors = self._data.setdefault("connectors", {})
        current = connectors.get(conn_id, {})
        bs_conn[f"{conn_id}.{timestamp}"] = dict(current) if isinstance(current, dict) else current

        # Apply draft to active
        connectors[conn_id] = dict(draft)
        self._save()
        return backup_key

    def confirm_apply(self, section: str, success: bool):
        """Confirm or rollback an apply operation."""
        if success:
            logger.info("Apply confirmed for '%s' — backup retained", section)
            return
        backups = self._data.get("_backups", {}).get("connectors", {})
        canon = self._draft_section(section)
        conn_id = canon.split(".", 1)[1] if "." in canon else canon
        backup_keys = sorted([k for k in backups if k.startswith(f"{conn_id}.")], reverse=True)
        if backup_keys:
            connectors = self._data.setdefault("connectors", {})
            connectors[conn_id] = dict(backups[backup_keys[0]])
            self._save()
            logger.info("Rolled back '%s' to backup %s", section, backup_keys[0])

    def rollback(self, section: str, backup_path: str | None = None):
        """Rollback a section to a specific backup."""
        backups = self._data.get("_backups", {}).get("connectors", {})
        canon = self._draft_section(section)
        conn_id = canon.split(".", 1)[1] if "." in canon else canon
        connectors = self._data.setdefault("connectors", {})
        if backup_path:
            # Extract connector key from backup_path
            for key in backups:
                if key == backup_path or key.endswith(backup_path):
                    connectors[conn_id] = dict(backups[key])
                    break
        else:
            backup_keys = sorted([k for k in backups if k.startswith(f"{conn_id}.")], reverse=True)
            if backup_keys:
                connectors[conn_id] = dict(backups[backup_keys[0]])
        self._save()
        logger.info("Rolled back '%s'", section)

    def export_sanitized(self) -> dict:
        """Export config with secrets masked."""
        safe = dict(self._data)
        if "api_key" in safe:
            safe["api_key"] = "***"
        return safe
