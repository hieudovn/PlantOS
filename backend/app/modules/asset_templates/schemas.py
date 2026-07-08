"""Asset Template & Binding — Pydantic schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# ---- Template Attribute ----

class TemplateAttribute(BaseModel):
    name: str
    display_name: Optional[str] = None
    required: bool = False
    data_type: str = "float"
    unit: Optional[str] = None
    category: str = "measurement"


# ---- Template Schemas ----

class TemplateCreate(BaseModel):
    template_id: str = Field(..., max_length=64, examples=["pump_template_v1"])
    name: str = Field(..., max_length=255)
    asset_type: str = Field(..., max_length=64)
    asset_role: str = Field("equipment", max_length=32)
    description: Optional[str] = None
    attributes: list[TemplateAttribute] = []
    domain_type: str = "generic"


class TemplateUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    attributes: Optional[list[TemplateAttribute]] = None
    status: Optional[str] = None


class TemplateResponse(BaseModel):
    template_id: str
    name: str
    asset_type: str
    asset_role: str
    description: Optional[str] = None
    attributes: list[dict]
    domain_type: str
    version: int
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ---- Binding Schemas ----

class BindingCreate(BaseModel):
    attribute_name: str = Field(..., max_length=128)
    signal_id: Optional[str] = None
    binding_type: str = "direct"


class BindingResponse(BaseModel):
    binding_id: str
    asset_id: str
    template_id: Optional[str] = None
    attribute_name: str
    signal_id: Optional[str] = None
    binding_type: str
    status: str
    validation_status: Optional[str] = None
    validation_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ValidationSummary(BaseModel):
    valid: bool
    errors: list[str] = []
    warnings: list[str] = []
