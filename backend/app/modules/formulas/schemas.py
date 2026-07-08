"""Formulas — Pydantic schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# ---- Formula Input ----

class FormulaInput(BaseModel):
    variable_name: str = Field(..., max_length=32, description="Variable name used in formula, e.g. A, B")
    signal_id: str = Field(..., max_length=256, description="Signal ID to bind")


# ---- Calculated Signal ----

class CalcSignalCreate(BaseModel):
    calc_signal_id: str = Field(..., max_length=128)
    asset_id: str = Field(..., max_length=128)
    name: str = Field(..., max_length=128)
    display_name: Optional[str] = None
    formula: str = Field(..., description="Formula expression")
    inputs: list[FormulaInput] = []
    output_signal_id: Optional[str] = None
    output_unit: Optional[str] = None
    execution_mode: str = "manual"
    status: str = "draft"


class CalcSignalUpdate(BaseModel):
    name: Optional[str] = None
    display_name: Optional[str] = None
    formula: Optional[str] = None
    inputs: Optional[list[FormulaInput]] = None
    output_signal_id: Optional[str] = None
    output_unit: Optional[str] = None
    execution_mode: Optional[str] = None
    status: Optional[str] = None


class CalcSignalResponse(BaseModel):
    calc_signal_id: str
    asset_id: str
    name: str
    display_name: Optional[str] = None
    formula: str
    inputs: list[dict] = []
    output_signal_id: Optional[str] = None
    output_unit: Optional[str] = None
    execution_mode: str
    status: str
    version: int
    last_run_at: Optional[datetime] = None
    last_run_status: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ---- KPI ----

class KpiCreate(BaseModel):
    kpi_id: str = Field(..., max_length=128)
    scope_type: str = Field(..., max_length=32, description="plant, area, or asset")
    scope_id: str = Field(..., max_length=128)
    name: str = Field(..., max_length=255)
    display_name: Optional[str] = None
    description: Optional[str] = None
    kpi_category: str = "operation"
    formula: str = Field(..., description="Formula expression")
    inputs: list[FormulaInput] = []
    unit: Optional[str] = None
    aggregation_window: Optional[str] = None
    target: Optional[float] = None
    warning_limit: Optional[float] = None
    critical_limit: Optional[float] = None
    display_priority: int = 0
    show_in_process_view: bool = False
    status: str = "draft"


class KpiUpdate(BaseModel):
    name: Optional[str] = None
    display_name: Optional[str] = None
    description: Optional[str] = None
    formula: Optional[str] = None
    inputs: Optional[list[FormulaInput]] = None
    unit: Optional[str] = None
    target: Optional[float] = None
    warning_limit: Optional[float] = None
    critical_limit: Optional[float] = None
    display_priority: Optional[int] = None
    show_in_process_view: Optional[bool] = None
    status: Optional[str] = None


class KpiResponse(BaseModel):
    kpi_id: str
    scope_type: str
    scope_id: str
    name: str
    display_name: Optional[str] = None
    description: Optional[str] = None
    kpi_category: str
    formula: str
    inputs: list[dict] = []
    unit: Optional[str] = None
    aggregation_window: Optional[str] = None
    target: Optional[float] = None
    warning_limit: Optional[float] = None
    critical_limit: Optional[float] = None
    display_priority: int
    show_in_process_view: bool
    status: str
    version: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ---- Formula Validation ----

class FormulaValidateRequest(BaseModel):
    formula: str
    input_names: list[str] = []


class FormulaValidateResponse(BaseModel):
    valid: bool
    errors: list[str] = []
    preview_value: Optional[float] = None


# ---- Execute/Test Results ----

class CalcSignalTestResult(BaseModel):
    status: str  # ok | error
    result: Optional[float] = None
    inputs: dict[str, float] = {}
    error: Optional[str] = None


class KpiCurrentValue(BaseModel):
    kpi_id: str
    name: str
    display_name: Optional[str] = None
    value: Optional[float] = None
    unit: Optional[str] = None
    target: Optional[float] = None
    warning_limit: Optional[float] = None
    critical_limit: Optional[float] = None
    status: Optional[str] = None  # good | warning | critical | unknown
