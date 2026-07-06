"""Asset Registry — Pydantic request/response schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# ---- Plant ----

class PlantCreate(BaseModel):
    plant_id: str = Field(..., max_length=64, examples=["DEMO-PLANT"])
    name: str = Field(..., max_length=255)
    location: Optional[str] = None
    timezone: str = "UTC"
    status: str = "active"


class PlantResponse(BaseModel):
    plant_id: str
    name: str
    location: Optional[str] = None
    timezone: str
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ---- Area ----

class AreaCreate(BaseModel):
    area_id: str = Field(..., max_length=64, examples=["PROCESS-AREA"])
    plant_id: str = Field(..., max_length=64)
    name: str = Field(..., max_length=255)
    area_type: Optional[str] = None
    status: str = "active"


class AreaResponse(BaseModel):
    area_id: str
    plant_id: str
    name: str
    area_type: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ---- Asset ----

class Location(BaseModel):
    lat: float
    lng: float


class AssetCreate(BaseModel):
    asset_id: str = Field(..., max_length=128, examples=["PUMP-101"])
    asset_code: Optional[str] = None
    name: str = Field(..., max_length=255)
    asset_type: str = Field(..., max_length=64)
    plant_id: Optional[str] = None  # business key, resolved to Plant
    area_id: Optional[str] = None   # business key, resolved to Area
    parent_asset_id: Optional[str] = None  # business key, self-ref
    criticality: str = "medium"
    lifecycle_status: str = "active"
    location: Optional[Location] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None


class AssetUpdate(BaseModel):
    name: Optional[str] = None
    asset_type: Optional[str] = None
    area_id: Optional[str] = None
    parent_asset_id: Optional[str] = None
    criticality: Optional[str] = None
    lifecycle_status: Optional[str] = None
    location: Optional[Location] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None


class AssetResponse(BaseModel):
    asset_id: str
    asset_code: Optional[str] = None
    name: str
    asset_type: str
    asset_role: Optional[str] = None  # v2.0+: functional_location | equipment | subsystem | component | logical_group
    plant_id: Optional[str] = None   # resolved from area→plant
    area_id: Optional[str] = None
    parent_asset_id: Optional[str] = None
    criticality: str
    lifecycle_status: str
    location: Optional[Location] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
