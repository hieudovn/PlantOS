"""Connector Registry — stub for E2V2-0.

Full BaseConnector interface + OPC UA / Modbus / MQTT implementations added in E2V2-2.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


class ConnectorRegistry:
    """Stub connector registry. No-op until E2V2-2."""

    def __init__(self, config):
        self.config = config
        self._connectors: dict[str, Any] = {}

    @property
    def active_count(self) -> int:
        return len(self._connectors)

    def list_status(self) -> list[dict]:
        return []

    async def start_all(self):
        pass

    async def stop_all(self):
        pass
