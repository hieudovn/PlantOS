"""Asset Registry — SQLAlchemy models for Plant, Area, Asset."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Float, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def _utcnow():
    return datetime.now(timezone.utc)


def _new_uuid():
    return uuid.uuid4()


class Plant(Base):
    __tablename__ = "plants"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=_new_uuid)
    plant_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    timezone: Mapped[str] = mapped_column(String(64), default="UTC")
    status: Mapped[str] = mapped_column(String(32), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    areas: Mapped[list[Area]] = relationship("Area", back_populates="plant", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Plant {self.plant_id}>"


class Area(Base):
    __tablename__ = "areas"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=_new_uuid)
    area_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    plant_id_fk: Mapped[uuid.UUID] = mapped_column(ForeignKey("plants.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    area_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    plant: Mapped[Plant] = relationship("Plant", back_populates="areas")
    assets: Mapped[list[Asset]] = relationship("Asset", back_populates="area", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Area {self.area_id}>"


class Asset(Base):
    __tablename__ = "assets"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=_new_uuid)
    asset_id: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    asset_code: Mapped[str | None] = mapped_column(String(128), nullable=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    asset_type: Mapped[str] = mapped_column(String(64), nullable=False)
    area_id_fk: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("areas.id"), nullable=True)
    parent_asset_id_fk: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("assets.id"), nullable=True)
    criticality: Mapped[str] = mapped_column(String(32), default="medium")
    lifecycle_status: Mapped[str] = mapped_column(String(32), default="active")
    location_lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    location_lng: Mapped[float | None] = mapped_column(Float, nullable=True)
    manufacturer: Mapped[str | None] = mapped_column(String(255), nullable=True)
    model: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    area: Mapped[Area | None] = relationship("Area", back_populates="assets")
    parent: Mapped[Asset | None] = relationship("Asset", remote_side="Asset.id", back_populates="children")
    children: Mapped[list[Asset]] = relationship("Asset", back_populates="parent", cascade="all, delete-orphan")
    signals: Mapped[list[Signal]] = relationship("Signal", back_populates="asset", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Asset {self.asset_id}>"
