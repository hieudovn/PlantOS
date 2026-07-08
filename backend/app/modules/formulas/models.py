"""Formulas — SQLAlchemy models."""

from datetime import datetime, timezone
from sqlalchemy import String, Text, Integer, Float, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


def _utcnow():
    return datetime.now(timezone.utc)


class CalculatedSignal(Base):
    __tablename__ = "calculated_signals"

    calc_signal_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    asset_id: Mapped[str] = mapped_column(String(128), ForeignKey("assets.asset_id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    formula: Mapped[str] = mapped_column(Text, nullable=False)
    formula_meta_json: Mapped[dict] = mapped_column(JSON, default=dict)
    inputs_json: Mapped[list | dict] = mapped_column(JSON, default=list)
    output_signal_id: Mapped[str | None] = mapped_column(String(256), nullable=True)
    output_unit: Mapped[str | None] = mapped_column(String(64), nullable=True)
    execution_mode: Mapped[str] = mapped_column(String(32), default="manual")
    schedule_interval: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="draft")
    version: Mapped[int] = mapped_column(Integer, default=1)
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_run_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)


class KpiDefinition(Base):
    __tablename__ = "kpi_definitions"

    kpi_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    scope_type: Mapped[str] = mapped_column(String(32), nullable=False)
    scope_id: Mapped[str] = mapped_column(String(128), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    kpi_category: Mapped[str] = mapped_column(String(32), default="operation")
    formula: Mapped[str] = mapped_column(Text, nullable=False)
    formula_meta_json: Mapped[dict] = mapped_column(JSON, default=dict)
    inputs_json: Mapped[list | dict] = mapped_column(JSON, default=list)
    unit: Mapped[str | None] = mapped_column(String(64), nullable=True)
    aggregation_window: Mapped[str | None] = mapped_column(String(32), nullable=True)
    target: Mapped[float | None] = mapped_column(Float, nullable=True)
    warning_limit: Mapped[float | None] = mapped_column(Float, nullable=True)
    critical_limit: Mapped[float | None] = mapped_column(Float, nullable=True)
    display_priority: Mapped[int] = mapped_column(Integer, default=0)
    show_in_process_view: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[str] = mapped_column(String(32), default="draft")
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)
