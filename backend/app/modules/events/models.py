"""CDM Event models — StateEvent, DowntimeEvent, ProductionEvent.

These follow the CDM (Common Data Model) defined in docs/20-data-model.md.
Each event type captures a distinct operational concern:
- StateEvent:      Discrete state transitions (running/stopped/alarm)
- DowntimeEvent:   Production loss events with duration tracking
- ProductionEvent: Production counts, totals, and batch completions
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Text, DateTime, Float, Integer, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


def _utcnow():
    return datetime.now(timezone.utc)


def _new_uuid():
    return uuid.uuid4()


class StateEvent(Base):
    """Discrete state transition event.

    Tracks when an asset changes operational state
    (e.g., running → stopped, auto → manual, alarm).
    """

    __tablename__ = "state_events"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=_new_uuid)
    event_id: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    asset_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    signal_id: Mapped[str | None] = mapped_column(String(256), nullable=True)
    previous_state: Mapped[str | None] = mapped_column(String(64), nullable=True)
    current_state: Mapped[str] = mapped_column(String(64), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    source: Mapped[str] = mapped_column(String(64), default="edge")
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    def __repr__(self):
        return f"<StateEvent {self.event_id} {self.previous_state}→{self.current_state}>"


class DowntimeEvent(Base):
    """Production loss event with duration tracking.

    Records when an asset enters a downtime state and when it recovers,
    enabling MTTR/MTBF calculations.
    """

    __tablename__ = "downtime_events"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=_new_uuid)
    event_id: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    asset_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    downtime_type: Mapped[str] = mapped_column(String(64), nullable=False)  # unplanned, planned, maintenance
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    source: Mapped[str] = mapped_column(String(64), default="edge")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    def __repr__(self):
        return f"<DowntimeEvent {self.event_id} type={self.downtime_type}>"


class ProductionEvent(Base):
    """Production count/total/batch event.

    Captures production metrics: counts, batch completions,
    quality totals, and production rates.
    """

    __tablename__ = "production_events"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=_new_uuid)
    event_id: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    asset_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)  # count, batch, quality, rate
    value: Mapped[float | None] = mapped_column(Float, nullable=True)
    unit: Mapped[str | None] = mapped_column(String(64), nullable=True)
    batch_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    product: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_quality_good: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    source: Mapped[str] = mapped_column(String(64), default="edge")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    def __repr__(self):
        return f"<ProductionEvent {self.event_id} type={self.event_type}>"
