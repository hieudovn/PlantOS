"""Signal Registry — SQLAlchemy repository layer."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.assets.models import Area, Asset, Plant
from app.modules.signals.models import Signal


class SignalRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, signal: Signal) -> Signal:
        self.session.add(signal)
        self.session.commit()
        self.session.refresh(signal)
        return signal

    def get_by_id(self, signal_id: str) -> Signal | None:
        return self.session.scalar(
            select(Signal).where(Signal.signal_id == signal_id)
        )

    def list_all(
        self,
        asset_id: str | None = None,
        signal_type: str | None = None,
        data_type: str | None = None,
        plant_id: str | None = None,
    ) -> list[Signal]:
        stmt = select(Signal)

        if plant_id:
            stmt = (
                stmt.join(Asset, Signal.asset_id_fk == Asset.id)
                .join(Area, Asset.area_id_fk == Area.id)
                .join(Plant, Area.plant_id_fk == Plant.id)
                .where(Plant.plant_id == plant_id)
            )
        elif asset_id:
            stmt = stmt.join(Asset).where(Asset.asset_id == asset_id)
        if signal_type:
            stmt = stmt.where(Signal.signal_type == signal_type)
        if data_type:
            stmt = stmt.where(Signal.data_type == data_type)
        return list(self.session.scalars(stmt).all())

    def update(self, signal: Signal, data: dict) -> Signal:
        for key, value in data.items():
            if value is not None:
                setattr(signal, key, value)
        self.session.commit()
        self.session.refresh(signal)
        return signal
