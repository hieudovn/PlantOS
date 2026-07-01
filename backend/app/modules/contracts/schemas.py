"""Contract v2 Pydantic models — mirrors JSON Schema."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class ContractMeta(BaseModel):
    version: str
    schema_version: str = "2.0"
    description: str


class SourceInfo(BaseModel):
    system_type: str  # virtual_factory | opcua | scada | manual | csv | engineering_tool
    system_name: str
    owner: Optional[str] = None
    generated_by: str
    generated_at: datetime


class PlantDef(BaseModel):
    plant_id: str
    plant_code: str
    name: str
    description: Optional[str] = None
    timezone: str = "UTC"
    status: str = "active"


class AreaDef(BaseModel):
    area_id: str
    area_code: str
    name: str
    plant_id: str


class AssetDef(BaseModel):
    asset_id: str
    asset_code: str
    name: str
    asset_type: str
    parent_asset_id: Optional[str] = None
    area_id: str
    criticality: str = "medium"
    status: str = "active"


class SignalDef(BaseModel):
    signal_id: str
    asset_id: str
    signal_name: str
    display_name: str
    signal_type: str = "measurement"
    data_type: str = "float"
    engineering_unit: str
    scale: float = 1.0
    offset: float = 0.0
    status: str = "active"


class UnsPolicy(BaseModel):
    namespace_root: str
    path_template: str
    normalize_case: str = "lower"
    separator: str = "/"


class ImportRecommendation(BaseModel):
    suggested_mode: str
    reason: str
    notes: Optional[str] = None


class OpcuaBinding(BaseModel):
    signal_id: str
    node_id: str
    scale: float = 1.0
    offset: float = 0.0


class Bindings(BaseModel):
    opcua: list[OpcuaBinding] = Field(default_factory=list)


class SimulationBehavior(BaseModel):
    signal_id: str
    pattern: str
    mid: Optional[float] = None
    amplitude: Optional[float] = None
    noise: Optional[float] = None
    frequency_hz: Optional[float] = None
    step_size: Optional[float] = None
    bounds_min: Optional[float] = None
    bounds_max: Optional[float] = None
    unit: Optional[str] = None


class Simulation(BaseModel):
    behaviors: dict[str, SimulationBehavior] = Field(default_factory=dict)


class ContractV2(BaseModel):
    contract: ContractMeta
    source: SourceInfo
    plant: PlantDef
    areas: list[AreaDef]
    assets: list[AssetDef]
    signals: list[SignalDef]
    uns: UnsPolicy
    import_recommendation: ImportRecommendation
    bindings: Optional[Bindings] = None
    simulation: Optional[Simulation] = None
    extensions: Optional[dict] = None
