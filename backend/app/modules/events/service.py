"""CDM Events — CRUD service."""

from datetime import datetime
from typing import Optional

from sqlalchemy import func

from app.db import get_session
from app.modules.events.models import StateEvent, DowntimeEvent, ProductionEvent


class StateEventService:
    """CRUD for StateEvent."""

    @staticmethod
    def create(data) -> StateEvent:
        with get_session() as session:
            event = StateEvent(
                event_id=data.event_id,
                asset_id=data.asset_id,
                signal_id=data.signal_id,
                previous_state=data.previous_state,
                current_state=data.current_state,
                reason=data.reason,
                source=data.source,
                occurred_at=data.occurred_at,
            )
            session.add(event)
            session.commit()
            session.refresh(event)
            return event

    @staticmethod
    def get_by_id(event_id: str) -> Optional[StateEvent]:
        with get_session() as session:
            return session.query(StateEvent).filter(
                StateEvent.event_id == event_id
            ).first()

    @staticmethod
    def list_by_asset(
        asset_id: str,
        skip: int = 0,
        limit: int = 50,
        from_ts: Optional[datetime] = None,
        to_ts: Optional[datetime] = None,
    ) -> tuple[list[StateEvent], int]:
        with get_session() as session:
            q = session.query(StateEvent).filter(
                StateEvent.asset_id == asset_id
            )
            if from_ts:
                q = q.filter(StateEvent.occurred_at >= from_ts)
            if to_ts:
                q = q.filter(StateEvent.occurred_at <= to_ts)
            total = q.count()
            items = (
                q.order_by(StateEvent.occurred_at.desc())
                .offset(skip)
                .limit(limit)
                .all()
            )
            return list(items), total


class DowntimeEventService:
    """CRUD for DowntimeEvent."""

    @staticmethod
    def create(data) -> DowntimeEvent:
        with get_session() as session:
            event = DowntimeEvent(
                event_id=data.event_id,
                asset_id=data.asset_id,
                downtime_type=data.downtime_type,
                reason=data.reason,
                started_at=data.started_at,
                ended_at=data.ended_at,
                duration_seconds=data.duration_seconds,
                source=data.source,
            )
            session.add(event)
            session.commit()
            session.refresh(event)
            return event

    @staticmethod
    def update(event_id: str, data) -> Optional[DowntimeEvent]:
        with get_session() as session:
            event = session.query(DowntimeEvent).filter(
                DowntimeEvent.event_id == event_id
            ).first()
            if not event:
                return None
            if data.ended_at is not None:
                event.ended_at = data.ended_at
            if data.duration_seconds is not None:
                event.duration_seconds = data.duration_seconds
            if data.reason is not None:
                event.reason = data.reason
            session.commit()
            session.refresh(event)
            return event

    @staticmethod
    def get_by_id(event_id: str) -> Optional[DowntimeEvent]:
        with get_session() as session:
            return session.query(DowntimeEvent).filter(
                DowntimeEvent.event_id == event_id
            ).first()

    @staticmethod
    def list_by_asset(
        asset_id: str,
        skip: int = 0,
        limit: int = 50,
        active_only: bool = False,
    ) -> tuple[list[DowntimeEvent], int]:
        with get_session() as session:
            q = session.query(DowntimeEvent).filter(
                DowntimeEvent.asset_id == asset_id
            )
            if active_only:
                q = q.filter(DowntimeEvent.ended_at.is_(None))
            total = q.count()
            items = (
                q.order_by(DowntimeEvent.started_at.desc())
                .offset(skip)
                .limit(limit)
                .all()
            )
            return list(items), total


class ProductionEventService:
    """CRUD for ProductionEvent."""

    @staticmethod
    def create(data) -> ProductionEvent:
        with get_session() as session:
            event = ProductionEvent(
                event_id=data.event_id,
                asset_id=data.asset_id,
                event_type=data.event_type,
                value=data.value,
                unit=data.unit,
                batch_id=data.batch_id,
                product=data.product,
                is_quality_good=data.is_quality_good,
                occurred_at=data.occurred_at,
                source=data.source,
            )
            session.add(event)
            session.commit()
            session.refresh(event)
            return event

    @staticmethod
    def get_by_id(event_id: str) -> Optional[ProductionEvent]:
        with get_session() as session:
            return session.query(ProductionEvent).filter(
                ProductionEvent.event_id == event_id
            ).first()

    @staticmethod
    def list_by_asset(
        asset_id: str,
        skip: int = 0,
        limit: int = 50,
        event_type: Optional[str] = None,
    ) -> tuple[list[ProductionEvent], int]:
        with get_session() as session:
            q = session.query(ProductionEvent).filter(
                ProductionEvent.asset_id == asset_id
            )
            if event_type:
                q = q.filter(ProductionEvent.event_type == event_type)
            total = q.count()
            items = (
                q.order_by(ProductionEvent.occurred_at.desc())
                .offset(skip)
                .limit(limit)
                .all()
            )
            return list(items), total
