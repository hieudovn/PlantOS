"""Asset Template & Binding — FastAPI router."""

from fastapi import APIRouter, HTTPException

from app.modules.asset_templates.schemas import (
    TemplateCreate, TemplateUpdate, TemplateResponse,
    BindingCreate, BindingResponse, ValidationSummary,
)
from app.modules.asset_templates.service import TemplateService, BindingService

router = APIRouter()
template_service = TemplateService()
binding_service = BindingService()


# ---- Templates ----

@router.post("/asset-templates", response_model=TemplateResponse, status_code=201)
def create_template(data: TemplateCreate):
    try:
        return template_service.create(data)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.get("/asset-templates", response_model=list[TemplateResponse])
def list_templates():
    return template_service.list_all()


@router.get("/asset-templates/{template_id}", response_model=TemplateResponse)
def get_template(template_id: str):
    try:
        return template_service.get(template_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.patch("/asset-templates/{template_id}", response_model=TemplateResponse)
def update_template(template_id: str, data: TemplateUpdate):
    try:
        return template_service.update(template_id, data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/asset-templates/{template_id}", status_code=204)
def delete_template(template_id: str):
    try:
        template_service.delete(template_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/asset-templates/seed", response_model=list[TemplateResponse])
def seed_templates():
    """Seed default templates (idempotent)."""
    return template_service.seed_defaults()


# ---- Bindings ----

@router.post("/assets/{asset_id}/bindings", response_model=BindingResponse, status_code=201)
def create_binding(asset_id: str, data: BindingCreate):
    try:
        return binding_service.create(asset_id, data)
    except ValueError as e:
        raise HTTPException(status_code=409 if "already exists" in str(e) else 404, detail=str(e))


@router.get("/assets/{asset_id}/bindings", response_model=list[BindingResponse])
def list_bindings(asset_id: str):
    return binding_service.list_for_asset(asset_id)


@router.delete("/assets/{asset_id}/bindings/{binding_id}", status_code=204)
def delete_binding(asset_id: str, binding_id: str):
    try:
        binding_service.delete(asset_id, binding_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/assets/{asset_id}/bindings/from-template/{template_id}", response_model=list[BindingResponse])
def bind_from_template(asset_id: str, template_id: str):
    """Auto-generate bindings from a template's attributes."""
    try:
        return binding_service.from_template(asset_id, template_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/assets/{asset_id}/bindings/validate", response_model=ValidationSummary)
def validate_bindings(asset_id: str):
    """Validate all bindings for an asset."""
    return binding_service.validate(asset_id)
