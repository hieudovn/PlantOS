"""Historian Service Interface — per ADR-0002."""

from abc import ABC, abstractmethod
from datetime import datetime

from app.modules.historian.models import (
    HistorianCapabilities,
    Measurement,
    WriteResult,
)


class HistorianInterface(ABC):
    """Abstract interface for PlantOS historian backends.

    Only TDengineHistorianAdapter implementation may know TDengine-specific
    schema, SQL, driver, or connection methods.
    """

    @abstractmethod
    async def write_measurements(self, measurements: list[Measurement]) -> WriteResult:
        """Write a batch of measurements. Must be idempotent where possible."""
        ...

    @abstractmethod
    async def query_latest(self, signal_ids: list[str]) -> dict[str, Measurement | None]:
        """Get latest measurement for each signal_id."""
        ...

    @abstractmethod
    async def query_history(
        self,
        signal_id: str,
        from_ts: datetime,
        to_ts: datetime,
        interval: str | None = None,
    ) -> list[Measurement]:
        """Query historical measurements for a single signal."""
        ...

    @abstractmethod
    async def query_multi_history(
        self,
        signal_ids: list[str],
        from_ts: datetime,
        to_ts: datetime,
        interval: str | None = None,
    ) -> dict[str, list[Measurement]]:
        """Query historical measurements for multiple signals."""
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the historian backend is reachable and healthy."""
        ...

    @abstractmethod
    def get_capabilities(self) -> HistorianCapabilities:
        """Return backend capabilities — per ADR-0002 capability model."""
        ...
