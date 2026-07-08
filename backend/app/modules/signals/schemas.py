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
    signal_category: str = Field("measurement", max_length=32)
    data_type: str = "float"
    engineering_unit: Optional[str] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    uns_path: Optional[str] = None
    source: Optional[SourceInfo] = None
    quality_policy: str = "GOOD"
    external_refs: Optional[dict] = Field(None, description="Opaque external references metadata")


class SignalUpdate(BaseModel):
    display_name: Optional[str] = None
    signal_type: Optional[str] = None
    signal_category: Optional[str] = Field(None, max_length=32)
    engineering_unit: Optional[str] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    uns_path: Optional[str] = None
    source: Optional[SourceInfo] = None
    quality_policy: Optional[str] = None
    external_refs: Optional[dict] = None


class SignalResponse(BaseModel):
    signal_id: str
    asset_id: str
    signal_name: str
    display_name: Optional[str] = None
    signal_type: str
    signal_category: str
    data_type: str
    engineering_unit: Optional[str] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    uns_path: Optional[str] = None
    source: Optional[SourceInfo] = None
    quality_policy: str
    external_refs: Optional[dict] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
