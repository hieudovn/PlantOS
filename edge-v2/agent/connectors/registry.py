"""ConnectorRegistry — registers connector classes, manages lifecycle.

CONNECTOR_REGISTRY maps type strings to connector classes.
Registry instantiates, starts, stops, and reports status for all connectors.
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any

from agent.connectors.base import BaseConnector, ConnectorStatus, TestResult

logger = logging.getLogger(__name__)

# Registry: type string → connector class
CONNECTOR_REGISTRY: dict[str, type[BaseConnector]] = {}


def register_connector_type(type_str: str, cls: type[BaseConnector]):
    """Register a connector class for a type string."""
    CONNECTOR_REGISTRY[type_str] = cls
    logger.debug("Registered connector type '%s' -> %s", type_str, cls.__name__)


class ConnectorRegistry:
    """Manages connector instances, lifecycle, and status reporting.

    Connectors are created from active config sections. Each connector
    is identified by its connector_id within the config.
    """

    def __init__(self, config):
        self.config = config
        self._connectors: dict[str, BaseConnector] = {}

    @property
    def active_count(self) -> int:
        return len(self._connectors)

    @property
    def all_ids(self) -> list[str]:
        return list(self._connectors.keys())

    # ---- Lifecycle ----------------------------------------------------------

    async def start_all(self):
        """Instantiate and start all configured connectors."""
        connectors_cfg = self.config.get("connectors", {})
        if not connectors_cfg:
            logger.info("No connectors configured")
            return

        for conn_id, conn_cfg in connectors_cfg.items():
            if not isinstance(conn_cfg, dict):
                continue
            conn_type = conn_cfg.get("type", "")
            if conn_type not in CONNECTOR_REGISTRY:
                logger.warning("Unknown connector type '%s' for '%s'", conn_type, conn_id)
                continue
            try:
                cls = CONNECTOR_REGISTRY[conn_type]
                instance = cls(conn_id, conn_cfg)
                self._connectors[conn_id] = instance
                if conn_cfg.get("enabled", True):
                    await instance.start()
                    logger.info("Started connector '%s' (type=%s)", conn_id, conn_type)
                else:
                    logger.info("Connector '%s' disabled, not starting", conn_id)
            except Exception as e:
                logger.exception("Failed to start connector '%s': %s", conn_id, e)

    async def stop_all(self):
        """Stop all running connectors."""
        for conn_id, instance in list(self._connectors.items()):
            try:
                await instance.stop()
                logger.info("Stopped connector '%s'", conn_id)
            except Exception as e:
                logger.exception("Error stopping connector '%s': %s", conn_id, e)
        self._connectors.clear()

    async def get_or_create(self, conn_id: str, conn_cfg: dict) -> BaseConnector | None:
        """Get existing or create new connector instance."""
        if conn_id in self._connectors:
            return self._connectors[conn_id]
        conn_type = conn_cfg.get("type", "")
        cls = CONNECTOR_REGISTRY.get(conn_type)
        if not cls:
            return None
        instance = cls(conn_id, conn_cfg)
        self._connectors[conn_id] = instance
        return instance

    async def remove(self, conn_id: str):
        """Stop and remove a connector."""
        instance = self._connectors.pop(conn_id, None)
        if instance:
            await instance.stop()

    # ---- Status -------------------------------------------------------------

    def get(self, conn_id: str) -> BaseConnector | None:
        return self._connectors.get(conn_id)

    async def get_status(self, conn_id: str) -> ConnectorStatus | None:
        instance = self._connectors.get(conn_id)
        if instance:
            return await instance.status()
        return None

    async def get_status_all(self) -> list[dict]:
        """Return status dicts for all connectors."""
        results = []
        for conn_id, instance in self._connectors.items():
            try:
                s = await instance.status()
                results.append({
                    "connector_id": s.connector_id,
                    "type": s.type,
                    "status": s.status,
                    "connected": s.connected,
                    "signal_count": s.signal_count,
                    "last_error": s.last_error,
                    "last_error_at": s.last_error_at.isoformat() if s.last_error_at else None,
                })
            except Exception as e:
                results.append({
                    "connector_id": conn_id,
                    "type": "unknown",
                    "status": "error",
                    "connected": False,
                    "signal_count": 0,
                    "last_error": str(e),
                    "last_error_at": datetime.now(timezone.utc).isoformat(),
                })
        return results

    def list_status_sync(self) -> list[dict]:
        """Synchronous fallback for status (used by heartbeat)."""
        results = []
        for conn_id, instance in self._connectors.items():
            try:
                results.append({
                    "connector_id": conn_id,
                    "type": getattr(instance, "connector_type", "unknown"),
                    "status": "running" if instance._running else "stopped",
                    "connected": True,
                    "signal_count": len(instance.config.get("tags", [])),
                    "last_error": None,
                })
            except Exception:
                pass
        return results
