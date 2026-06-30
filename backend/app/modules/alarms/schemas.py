"""Alarm Rule Engine — Pydantic schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class AlarmRuleCreate(BaseModel):
    rule_id: str = Field(..., max_length=128, examples=["pump-high-pressure"])
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    trigger_type: str = "threshold"
    signal_id: str = Field(..., max_length=256)
    asset_id: Optional[str] = None
    condition: str = ">"
    threshold: float
    hysteresis: float = 0.5
    delay_seconds: int = 5
    severity: str = "medium"
    message_template: Optional[str] = None
    auto_clear: bool = True
    clear_threshold: Optional[float] = None
    status: str = "active"


class AlarmRuleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    condition: Optional[str] = None
    threshold: Optional[float] = None
    hysteresis: Optional[float] = None
    delay_seconds: Optional[int] = None
    severity: Optional[str] = None
    message_template: Optional[str] = None
    auto_clear: Optional[bool] = None
    clear_threshold: Optional[float] = None
    status: Optional[str] = None


class AlarmRuleResponse(BaseModel):
    rule_id: str
    name: str
    description: Optional[str] = None
    trigger_type: str
    signal_id: str
    asset_id: Optional[str] = None
    condition: str
    threshold: float
    hysteresis: float
    delay_seconds: int
    severity: str
    message_template: Optional[str] = None
    auto_clear: bool
    clear_threshold: Optional[float] = None
    status: str
    version: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AlarmEventResponse(BaseModel):
    alarm_id: str
    rule_id: str
    asset_id: Optional[str] = None
    signal_id: str
    severity: str
    state: str
    message: Optional[str] = None
    trigger_value: Optional[float] = None
    started_at: datetime
    acknowledged_at: Optional[datetime] = None
    cleared_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class CalcRuleCreate(BaseModel):
    rule_id: str = Field(..., max_length=128, examples=["feeder-power"])
    name: str = Field(..., max_length=255)
    signal_id: str = Field(..., max_length=256)
    formula: str = Field(..., description="e.g. FEEDER-01.voltage * FEEDER-01.current")
    interval_seconds: int = 10
