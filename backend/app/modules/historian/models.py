"""Historian domain models — canonical Measurement object."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class Quality(str, Enum):
    """Measurement quality values per OPC UA / PlantOS convention."""
    GOOD = "GOOD"
    BAD = "BAD"
    UNCERTAIN = "UNCERTAIN"
    STALE = "STALE"
    SIMULATED = "SIMULATED"
    MANUAL = "MANUAL"
    ESTIMATED = "ESTIMATED"
    MISSING = "MISSING"


class Measurement(BaseModel):
    """Canonical measurement object — matches docs/20-data-model.md §3."""
    timestamp: datetime
    signal_id: str
    value: float | bool | None = None
    quality: Quality = Quality.GOOD
    source: str = "unknown"


class HistorianCapabilities(BaseModel):
    """Capabilities exposed by a historian backend — per ADR-0002."""
    backend: str
    supports_write: bool = True
    supports_batch_write: bool = True
    supports_latest_query: bool = True
    supports_aggregation: bool = False
    supports_downsampling: bool = False
    supports_backfill: bool = False
    supports_string_values: bool = False
    supports_quality: bool = True
    supports_external_tag_mapping: bool = False


class WriteResult(BaseModel):
    """Result of a batch write operation."""
    accepted: int = 0
    rejected: int = 0
    errors: list[str] = Field(default_factory=list)
