"""Alarm Rule Engine — SQLAlchemy models."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Text, DateTime, ForeignKey, Boolean, Integer, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def _utcnow():
    return datetime.now(timezone.utc)


def _new_uuid():
    return uuid.uuid4()


class AlarmRule(Base):
    __tablename__ = "alarm_rules"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=_new_uuid)
    rule_id: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    trigger_type: Mapped[str] = mapped_column(String(32), default="threshold")
    signal_id: Mapped[str] = mapped_column(String(256), nullable=False)
    asset_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    condition: Mapped[str] = mapped_column(String(8), default=">")
    threshold: Mapped[float] = mapped_column(Float, nullable=False)
    hysteresis: Mapped[float] = mapped_column(Float, default=0.5)
    delay_seconds: Mapped[int] = mapped_column(Integer, default=5)
    severity: Mapped[str] = mapped_column(String(32), default="medium")
    message_template: Mapped[str | None] = mapped_column(Text, nullable=True)
    auto_clear: Mapped[bool] = mapped_column(Boolean, default=True)
    clear_threshold: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="active")
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    alarms: Mapped[list["AlarmEvent"]] = relationship("AlarmEvent", back_populates="rule", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<AlarmRule {self.rule_id}>"


class AlarmEvent(Base):
    __tablename__ = "alarm_events"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=_new_uuid)
    alarm_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    rule_id_fk: Mapped[uuid.UUID] = mapped_column(ForeignKey("alarm_rules.id"), nullable=False)
    asset_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    signal_id: Mapped[str] = mapped_column(String(256), nullable=False)
    severity: Mapped[str] = mapped_column(String(32), default="medium")
    state: Mapped[str] = mapped_column(String(32), default="active")
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    trigger_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cleared_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    rule: Mapped["AlarmRule"] = relationship("AlarmRule", back_populates="alarms")

    def __repr__(self):
        return f"<AlarmEvent {self.alarm_id} state={self.state}>"
