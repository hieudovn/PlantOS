"""Signal Registry — Pydantic request/response schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class SourceInfo(BaseModel):
    """Source reference — separates semantic signal from raw protocol."""
    source_type: str = "simulator"
    source_ref: Optional[str] = None


class SignalCreate(BaseModel):
    signal_id: str = Field(..., max_length=256, examples=["PUMP-101.discharge_pressure"])
    asset_id: str = Field(..., max_length=128)  # business key
    signal_name: str = Field(..., max_length=128)
    display_name: Optional[str] = None
    signal_type: str = "measurement"
    data_type: str = "float"
    engineering_unit: Optional[str] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    uns_path: Optional[str] = None
    source: Optional[SourceInfo] = None
    quality_policy: str = "GOOD"


class SignalUpdate(BaseModel):
    display_name: Optional[str] = None
    signal_type: Optional[str] = None
    engineering_unit: Optional[str] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    uns_path: Optional[str] = None
    source: Optional[SourceInfo] = None
    quality_policy: Optional[str] = None


class SignalResponse(BaseModel):
    signal_id: str
    asset_id: str
    signal_name: str
    display_name: Optional[str] = None
    signal_type: str
    signal_category: Optional[str] = None  # v2.0+: measurement | status | alarm | counter | calculated | command
    data_type: str
    engineering_unit: Optional[str] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    uns_path: Optional[str] = None
    source: Optional[SourceInfo] = None
    external_refs: Optional[dict] = None   # v2.0+: opaque metadata for external systems
    quality_policy: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
