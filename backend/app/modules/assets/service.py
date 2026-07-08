"""Asset Registry — Service layer (business logic + validation)."""

from app.db import get_session
from app.modules.assets.models import Plant, Area, Asset
from app.modules.assets.repository import (
    PlantRepository,
    AreaRepository,
    AssetRepository,
)
from app.modules.assets.schemas import (
    PlantCreate,
    PlantResponse,
    AreaCreate,
    AreaUpdate,
    AreaResponse,
    AssetCreate,
    AssetUpdate,
    AssetResponse,
    Location,
)


# ---- Helpers ----

def _plant_to_response(plant: Plant) -> PlantResponse:
    return PlantResponse.model_validate(plant)


def _area_to_response(area: Area) -> AreaResponse:
    return AreaResponse(
        area_id=area.area_id,
        plant_id=area.plant.plant_id,
        name=area.name,
        area_type=area.area_type,
        status=area.status,
        created_at=area.created_at,
        updated_at=area.updated_at,
    )


def _asset_to_response(asset: Asset) -> AssetResponse:
    plant_id = None
    area_id = None
    if asset.area:
        area_id = asset.area.area_id
        if asset.area.plant:
            plant_id = asset.area.plant.plant_id

    location = None
    if asset.location_lat is not None and asset.location_lng is not None:
        location = Location(lat=asset.location_lat, lng=asset.location_lng)

    return AssetResponse(
        asset_id=asset.asset_id,
        asset_code=asset.asset_code,
        name=asset.name,
        asset_type=asset.asset_type,
        asset_role=asset.asset_role,
        plant_id=plant_id,
        area_id=area_id,
        parent_asset_id=asset.parent.asset_id if asset.parent else None,
        criticality=asset.criticality,
        lifecycle_status=asset.lifecycle_status,
        location=location,
        manufacturer=asset.manufacturer,
        model=asset.model,
        created_at=asset.created_at,
        updated_at=asset.updated_at,
    )


# ---- Plant Service ----

class PlantService:
    def create_plant(self, data: PlantCreate) -> PlantResponse:
        with get_session() as session:
            repo = PlantRepository(session)
            if repo.get_by_id(data.plant_id):
                raise ValueError(f"Plant '{data.plant_id}' already exists")
            plant = Plant(
                plant_id=data.plant_id,
                name=data.name,
                location=data.location,
                timezone=data.timezone,
                status=data.status,
            )
            plant = repo.create(plant)
            return _plant_to_response(plant)

    def get_plant(self, plant_id: str) -> PlantResponse:
        with get_session() as session:
            repo = PlantRepository(session)
            plant = repo.get_by_id(plant_id)
            if not plant:
                raise ValueError(f"Plant '{plant_id}' not found")
            return _plant_to_response(plant)

    def list_plants(self) -> list[PlantResponse]:
        with get_session() as session:
            repo = PlantRepository(session)
            plants = repo.list_all()
            return [_plant_to_response(p) for p in plants]


# ---- Area Service ----

class AreaService:
    def create_area(self, data: AreaCreate) -> AreaResponse:
        with get_session() as session:
            plant_repo = PlantRepository(session)
            plant = plant_repo.get_by_id(data.plant_id)
            if not plant:
                raise ValueError(f"Plant '{data.plant_id}' not found")

            area_repo = AreaRepository(session)
            if area_repo.get_by_id(data.area_id):
                raise ValueError(f"Area '{data.area_id}' already exists")

            area = Area(
                area_id=data.area_id,
                plant_id_fk=plant.id,
                name=data.name,
                area_type=data.area_type,
                status=data.status,
            )
            area = area_repo.create(area)
            return _area_to_response(area)

    def get_area(self, area_id: str) -> AreaResponse:
        with get_session() as session:
            repo = AreaRepository(session)
            area = repo.get_by_id(area_id)
            if not area:
                raise ValueError(f"Area '{area_id}' not found")
            return _area_to_response(area)

    def list_areas(self, plant_id: str | None = None) -> list[AreaResponse]:
        with get_session() as session:
            repo = AreaRepository(session)
            areas = repo.list_by_plant(plant_id)
            return [_area_to_response(a) for a in areas]

    def update_area(self, area_id: str, data: AreaUpdate) -> AreaResponse:
        """Update area metadata."""
        with get_session() as session:
            repo = AreaRepository(session)
            area = repo.get_by_id(area_id)
            if not area:
                raise ValueError(f"Area '{area_id}' not found")
            update_data = data.model_dump(exclude_unset=True)
            for key, value in update_data.items():
                if value is not None:
                    setattr(area, key, value)
            session.commit()
            session.refresh(area)
            return _area_to_response(area)


# ---- Asset Service ----

class AssetService:
    def create_asset(self, data: AssetCreate) -> AssetResponse:
        with get_session() as session:
            asset_repo = AssetRepository(session)
            if asset_repo.get_by_id(data.asset_id):
                raise ValueError(f"Asset '{data.asset_id}' already exists")

            # Resolve area
            area = None
            if data.area_id:
                area_repo = AreaRepository(session)
                area = area_repo.get_by_id(data.area_id)
                if not area:
                    raise ValueError(f"Area '{data.area_id}' not found")

            # Resolve parent
            parent = None
            if data.parent_asset_id:
                parent = asset_repo.get_by_id(data.parent_asset_id)
                if not parent:
                    raise ValueError(f"Parent asset '{data.parent_asset_id}' not found")

            location_lat = data.location.lat if data.location else None
            location_lng = data.location.lng if data.location else None

            asset = Asset(
                asset_id=data.asset_id,
                asset_code=data.asset_code,
                name=data.name,
                asset_type=data.asset_type,
                area_id_fk=area.id if area else None,
                parent_asset_id_fk=parent.id if parent else None,
                criticality=data.criticality,
                lifecycle_status=data.lifecycle_status,
                location_lat=location_lat,
                location_lng=location_lng,
                manufacturer=data.manufacturer,
                model=data.model,
            )
            asset = asset_repo.create(asset)
            return _asset_to_response(asset)

    def get_asset(self, asset_id: str) -> AssetResponse:
        with get_session() as session:
            repo = AssetRepository(session)
            asset = repo.get_by_id(asset_id)
            if not asset:
                raise ValueError(f"Asset '{asset_id}' not found")
            return _asset_to_response(asset)

    def list_assets(
        self,
        plant_id: str | None = None,
        area_id: str | None = None,
        asset_type: str | None = None,
    ) -> list[AssetResponse]:
        with get_session() as session:
            repo = AssetRepository(session)
            assets = repo.list_all(
                plant_id=plant_id, area_id=area_id, asset_type=asset_type
            )
            return [_asset_to_response(a) for a in assets]

    def update_asset(self, asset_id: str, data: AssetUpdate) -> AssetResponse:
        with get_session() as session:
            asset_repo = AssetRepository(session)
            asset = asset_repo.get_by_id(asset_id)
            if not asset:
                raise ValueError(f"Asset '{asset_id}' not found")

            update_data = data.model_dump(exclude_unset=True)

            # Resolve area if changing
            if "area_id" in update_data:
                aid = update_data.pop("area_id")
                if aid:
                    area_repo = AreaRepository(session)
                    area = area_repo.get_by_id(aid)
                    if not area:
                        raise ValueError(f"Area '{aid}' not found")
                    update_data["area_id_fk"] = area.id
                else:
                    update_data["area_id_fk"] = None

            # Resolve parent if changing
            if "parent_asset_id" in update_data:
                pid = update_data.pop("parent_asset_id")
                if pid:
                    parent = asset_repo.get_by_id(pid)
                    if not parent:
                        raise ValueError(f"Parent asset '{pid}' not found")
                    update_data["parent_asset_id_fk"] = parent.id
                else:
                    update_data["parent_asset_id_fk"] = None

            # Flatten location
            if "location" in update_data:
                loc = update_data.pop("location")
                update_data["location_lat"] = loc.lat if loc else None
                update_data["location_lng"] = loc.lng if loc else None

            asset = asset_repo.update(asset, update_data)
            return _asset_to_response(asset)

    def delete_asset(self, asset_id: str) -> None:
        """Soft-delete an asset by setting lifecycle_status='deleted'."""
        with get_session() as session:
            repo = AssetRepository(session)
            asset = repo.get_by_id(asset_id)
            if not asset:
                raise ValueError(f"Asset '{asset_id}' not found")
            repo.update(asset, {"lifecycle_status": "deleted"})
