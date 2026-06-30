"""Asset Registry — SQLAlchemy repository layer."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.assets.models import Plant, Area, Asset


class PlantRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, plant: Plant) -> Plant:
        self.session.add(plant)
        self.session.commit()
        self.session.refresh(plant)
        return plant

    def get_by_id(self, plant_id: str) -> Plant | None:
        return self.session.scalar(
            select(Plant).where(Plant.plant_id == plant_id)
        )

    def list_all(self) -> list[Plant]:
        return list(self.session.scalars(select(Plant)).all())


class AreaRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, area: Area) -> Area:
        self.session.add(area)
        self.session.commit()
        self.session.refresh(area)
        return area

    def get_by_id(self, area_id: str) -> Area | None:
        return self.session.scalar(
            select(Area).where(Area.area_id == area_id)
        )

    def list_by_plant(self, plant_id: str | None = None) -> list[Area]:
        stmt = select(Area)
        if plant_id:
            stmt = stmt.join(Plant).where(Plant.plant_id == plant_id)
        return list(self.session.scalars(stmt).all())


class AssetRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, asset: Asset) -> Asset:
        self.session.add(asset)
        self.session.commit()
        self.session.refresh(asset)
        return asset

    def get_by_id(self, asset_id: str) -> Asset | None:
        return self.session.scalar(
            select(Asset).where(Asset.asset_id == asset_id)
        )

    def list_all(
        self,
        plant_id: str | None = None,
        area_id: str | None = None,
        asset_type: str | None = None,
    ) -> list[Asset]:
        stmt = select(Asset)
        if area_id:
            stmt = stmt.join(Area).where(Area.area_id == area_id)
        if plant_id:
            stmt = stmt.join(Area).join(Plant).where(Plant.plant_id == plant_id)
        if asset_type:
            stmt = stmt.where(Asset.asset_type == asset_type)
        return list(self.session.scalars(stmt).all())

    def update(self, asset: Asset, data: dict) -> Asset:
        for key, value in data.items():
            if value is not None:
                setattr(asset, key, value)
        self.session.commit()
        self.session.refresh(asset)
        return asset
