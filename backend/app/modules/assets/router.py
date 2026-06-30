"""Asset Registry — FastAPI router."""

from fastapi import APIRouter, HTTPException, Query

from app.modules.assets.schemas import (
    PlantCreate,
    PlantResponse,
    AreaCreate,
    AreaResponse,
    AssetCreate,
    AssetUpdate,
    AssetResponse,
)
from app.modules.assets.service import PlantService, AreaService, AssetService

router = APIRouter()

plant_service = PlantService()
area_service = AreaService()
asset_service = AssetService()


# ---- Plants ----

@router.post("/plants", response_model=PlantResponse, status_code=201)
def create_plant(data: PlantCreate):
    try:
        return plant_service.create_plant(data)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.get("/plants", response_model=list[PlantResponse])
def list_plants():
    return plant_service.list_plants()


@router.get("/plants/{plant_id}", response_model=PlantResponse)
def get_plant(plant_id: str):
    try:
        return plant_service.get_plant(plant_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ---- Areas ----

@router.post("/areas", response_model=AreaResponse, status_code=201)
def create_area(data: AreaCreate):
    try:
        return area_service.create_area(data)
    except ValueError as e:
        raise HTTPException(
            status_code=409 if "already" in str(e) else 404, detail=str(e)
        )


@router.get("/areas", response_model=list[AreaResponse])
def list_areas(plant_id: str | None = Query(None)):
    return area_service.list_areas(plant_id)


@router.get("/areas/{area_id}", response_model=AreaResponse)
def get_area(area_id: str):
    try:
        return area_service.get_area(area_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ---- Assets ----

@router.post("/assets", response_model=AssetResponse, status_code=201)
def create_asset(data: AssetCreate):
    try:
        return asset_service.create_asset(data)
    except ValueError as e:
        raise HTTPException(
            status_code=409 if "already" in str(e) else 404, detail=str(e)
        )


@router.get("/assets", response_model=list[AssetResponse])
def list_assets(
    plant_id: str | None = Query(None),
    area_id: str | None = Query(None),
    asset_type: str | None = Query(None),
):
    return asset_service.list_assets(
        plant_id=plant_id, area_id=area_id, asset_type=asset_type
    )


@router.get("/assets/{asset_id}", response_model=AssetResponse)
def get_asset(asset_id: str):
    try:
        return asset_service.get_asset(asset_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.patch("/assets/{asset_id}", response_model=AssetResponse)
def update_asset(asset_id: str, data: AssetUpdate):
    try:
        return asset_service.update_asset(asset_id, data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
