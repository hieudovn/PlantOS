"""Measurement — Pydantic request/response schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class MeasurementPoint(BaseModel):
    """Single measurement data point for ingestion."""
    timestamp: datetime
    signal_id: str
    value: float | bool
    quality: str = "GOOD"


class IngestRequest(BaseModel):
    """Batch measurement ingestion request — matches API contract."""
    source: str = "unknown"
    measurements: list[MeasurementPoint]


class IngestResponse(BaseModel):
    """Batch ingestion result."""
    accepted: int
    rejected: int
    errors: list[str] = Field(default_factory=list)


class CurrentValueResponse(BaseModel):
    """Current value for a single signal."""
    signal_id: str
    asset_id: Optional[str] = None
    timestamp: Optional[datetime] = None
    value: Optional[float | bool] = None
    quality: Optional[str] = None
    source: Optional[str] = None


class HistoryQueryParams(BaseModel):
    """Query parameters for historical data."""
    signal_id: str
    from_ts: datetime
    to_ts: datetime
    interval: Optional[str] = None  # e.g., "1m", "5m", "1h"


class HistoryResponse(BaseModel):
    """Historical data response."""
    signal_id: str
    data: list[CurrentValueResponse] = Field(default_factory=list)
