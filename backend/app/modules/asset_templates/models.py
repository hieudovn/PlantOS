"""Asset Template & Binding — SQLAlchemy models."""

import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Text, Integer, DateTime, ForeignKey, JSON, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


def _utcnow():
    return datetime.now(timezone.utc)


def _new_uuid():
    return uuid.uuid4()


class AssetTemplate(Base):
    __tablename__ = "asset_templates"

    template_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    asset_type: Mapped[str] = mapped_column(String(64), nullable=False)
    asset_role: Mapped[str] = mapped_column(String(32), default="equipment")
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    attributes_json: Mapped[dict | list] = mapped_column(JSON, default=list)
    domain_type: Mapped[str] = mapped_column(String(32), default="generic")
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    version: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String(32), default="draft")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)


class AssetAttributeBinding(Base):
    __tablename__ = "asset_attribute_bindings"
    __table_args__ = (UniqueConstraint("asset_id", "attribute_name"),)

    binding_id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=_new_uuid)
    asset_id: Mapped[str] = mapped_column(String(128), ForeignKey("assets.asset_id", ondelete="CASCADE"), nullable=False)
    template_id: Mapped[str | None] = mapped_column(String(64), ForeignKey("asset_templates.template_id"), nullable=True)
    attribute_name: Mapped[str] = mapped_column(String(128), nullable=False)
    signal_id: Mapped[str | None] = mapped_column(String(256), ForeignKey("signals.signal_id", ondelete="SET NULL"), nullable=True)
    binding_type: Mapped[str] = mapped_column(String(32), default="direct")
    status: Mapped[str] = mapped_column(String(32), default="active")
    validation_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    validation_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)
