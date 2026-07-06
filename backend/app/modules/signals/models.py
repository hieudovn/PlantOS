"""Signal Registry — SQLAlchemy model for Signal."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Float, ForeignKey, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def _utcnow():
    return datetime.now(timezone.utc)


def _new_uuid():
    return uuid.uuid4()


class Signal(Base):
    __tablename__ = "signals"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=_new_uuid)
    signal_id: Mapped[str] = mapped_column(String(256), unique=True, nullable=False, index=True)
    asset_id_fk: Mapped[uuid.UUID] = mapped_column(ForeignKey("assets.id"), nullable=False)
    signal_name: Mapped[str] = mapped_column(String(128), nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    signal_type: Mapped[str] = mapped_column(String(32), default="measurement")
    signal_category: Mapped[str | None] = mapped_column(String(32), nullable=True, default="measurement")
    external_refs: Mapped[dict | None] = mapped_column(JSON, nullable=True, default=dict)
    data_type: Mapped[str] = mapped_column(String(32), default="float")
    engineering_unit: Mapped[str | None] = mapped_column(String(64), nullable=True)
    min_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    max_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    uns_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    source_type: Mapped[str] = mapped_column(String(64), default="simulator")
    source_ref: Mapped[str | None] = mapped_column(String(512), nullable=True)
    quality_policy: Mapped[str] = mapped_column(String(32), default="GOOD")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    asset: Mapped[Asset] = relationship("Asset", back_populates="signals")

    def __repr__(self):
        return f"<Signal {self.signal_id}>"
