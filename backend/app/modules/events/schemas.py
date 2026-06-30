"""CDM Events — Pydantic schemas for API serialization."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# ---- StateEvent Schemas ----

class StateEventCreate(BaseModel):
    event_id: str = Field(..., max_length=128)
    asset_id: str = Field(..., max_length=128)
    signal_id: Optional[str] = Field(None, max_length=256)
    previous_state: Optional[str] = Field(None, max_length=64)
    current_state: str = Field(..., max_length=64)
    reason: Optional[str] = None
    source: str = Field("edge", max_length=64)
    occurred_at: datetime


class StateEventUpdate(BaseModel):
    current_state: Optional[str] = Field(None, max_length=64)
    reason: Optional[str] = None


class StateEventResponse(BaseModel):
    id: str
    event_id: str
    asset_id: str
    signal_id: Optional[str] = None
    previous_state: Optional[str] = None
    current_state: str
    reason: Optional[str] = None
    source: str
    occurred_at: datetime
    created_at: datetime

    model_config = {"from_attributes": True}


# ---- DowntimeEvent Schemas ----

class DowntimeEventCreate(BaseModel):
    event_id: str = Field(..., max_length=128)
    asset_id: str = Field(..., max_length=128)
    downtime_type: str = Field(..., max_length=64)  # unplanned, planned, maintenance
    reason: Optional[str] = None
    started_at: datetime
    ended_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    source: str = Field("edge", max_length=64)


class DowntimeEventUpdate(BaseModel):
    ended_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    reason: Optional[str] = None


class DowntimeEventResponse(BaseModel):
    id: str
    event_id: str
    asset_id: str
    downtime_type: str
    reason: Optional[str] = None
    started_at: datetime
    ended_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    source: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ---- ProductionEvent Schemas ----

class ProductionEventCreate(BaseModel):
    event_id: str = Field(..., max_length=128)
    asset_id: str = Field(..., max_length=128)
    event_type: str = Field(..., max_length=64)  # count, batch, quality, rate
    value: Optional[float] = None
    unit: Optional[str] = Field(None, max_length=64)
    batch_id: Optional[str] = Field(None, max_length=128)
    product: Optional[str] = Field(None, max_length=255)
    is_quality_good: Optional[bool] = None
    occurred_at: datetime
    source: str = Field("edge", max_length=64)


class ProductionEventResponse(BaseModel):
    id: str
    event_id: str
    asset_id: str
    event_type: str
    value: Optional[float] = None
    unit: Optional[str] = None
    batch_id: Optional[str] = None
    product: Optional[str] = None
    is_quality_good: Optional[bool] = None
    occurred_at: datetime
    source: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ---- Generic list wrapper ----

class EventListResponse(BaseModel):
    items: list
    total: int
