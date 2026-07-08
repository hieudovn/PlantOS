"""BaseConnector interface — unified contract for all protocol connectors.

All connectors (OPC UA, Modbus TCP, MQTT Subscribe) implement this interface.
RawReading is the universal output type consumed by ProcessingEngine.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal


@dataclass
class RawReading:
    """Output from a connector, input to processing engine."""
    source_ref: str           # Protocol-specific: NodeId, register, topic
    signal_id: str
    raw_value: float
    timestamp: datetime
    quality_hint: str | None = "GOOD"  # GOOD / UNCERTAIN / BAD


@dataclass
class TagConfig:
    """A single tag/signal mapping within a connector."""
    tag_id: str               # Unique ID within this connector
    source_ref: str           # Protocol address (NodeId, register, topic path)
    signal_id: str            # PlantOS signal_id (must match Center)
    data_type: str = "float"  # float, int, bool, uint32
    scale: float = 1.0
    offset: float = 0.0
    poll_interval_ms: int = 1000
    enabled: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ConnectorStatus:
    """Runtime status of a connector."""
    connector_id: str
    type: str
    status: Literal["running", "stopped", "error", "degraded"] = "stopped"
    connected: bool = False
    signal_count: int = 0
    last_success_at: datetime | None = None
    last_error: str | None = None
    last_error_at: datetime | None = None


@dataclass
class TestResult:
    """Result of a test_connection() call."""
    success: bool
    message: str = ""
    detail: str = ""
    latency_ms: float = 0.0


class BaseConnector(ABC):
    """Abstract base for all protocol connectors.

    Lifecycle: start → (read_tags loop) → stop.
    Config changes go through safe apply: validate → test → apply → confirm.
    """

    def __init__(self, connector_id: str, config: dict):
        self.connector_id = connector_id
        self.connector_type: str = ""
        self.config = config
        self._running = False

    @abstractmethod
    async def start(self) -> None:
        """Start the connector. Begin polling/subscribing."""

    @abstractmethod
    async def stop(self) -> None:
        """Stop the connector gracefully."""

    async def restart(self) -> None:
        """Restart the connector."""
        await self.stop()
        await self.start()

    @abstractmethod
    async def status(self) -> ConnectorStatus:
        """Return current runtime status."""

    @abstractmethod
    async def test_connection(self) -> TestResult:
        """Test the connection without starting the connector."""

    @abstractmethod
    async def validate_config(self, config: dict) -> list[str]:
        """Validate a connector config. Returns list of error messages."""

    @abstractmethod
    async def read_tags(self, tag_configs: list[TagConfig]) -> list[RawReading]:
        """Read specified tags and return RawReadings."""

    @abstractmethod
    async def browse(self, path: str = "") -> list[dict[str, Any]]:
        """Browse discoverable nodes/tags (protocol-specific). Returns list of
        {node_id, display_name, type, has_children} dicts."""
