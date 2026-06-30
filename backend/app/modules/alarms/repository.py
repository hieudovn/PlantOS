"""Alarm Rule Engine — SQLAlchemy repository layer."""

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.modules.alarms.models import AlarmRule, AlarmEvent


class AlarmRuleRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, rule: AlarmRule) -> AlarmRule:
        self.session.add(rule)
        self.session.commit()
        self.session.refresh(rule)
        return rule

    def get_by_id(self, rule_id: str) -> AlarmRule | None:
        return self.session.scalar(select(AlarmRule).where(AlarmRule.rule_id == rule_id))

    def list_all(self, status: str | None = None) -> list[AlarmRule]:
        stmt = select(AlarmRule)
        if status:
            stmt = stmt.where(AlarmRule.status == status)
        return list(self.session.scalars(stmt).all())

    def update(self, rule: AlarmRule, data: dict) -> AlarmRule:
        for key, value in data.items():
            if value is not None:
                setattr(rule, key, value)
        rule.version += 1
        self.session.commit()
        self.session.refresh(rule)
        return rule

    def delete(self, rule: AlarmRule):
        self.session.delete(rule)
        self.session.commit()


class AlarmEventRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, event: AlarmEvent) -> AlarmEvent:
        self.session.add(event)
        self.session.commit()
        self.session.refresh(event)
        return event

    def get_by_id(self, alarm_id: str) -> AlarmEvent | None:
        return self.session.scalar(select(AlarmEvent).where(AlarmEvent.alarm_id == alarm_id))

    def list_all(
        self, state: str | None = None, severity: str | None = None, limit: int = 100
    ) -> list[AlarmEvent]:
        stmt = select(AlarmEvent).order_by(AlarmEvent.started_at.desc()).limit(limit)
        if state:
            stmt = stmt.where(AlarmEvent.state == state)
        if severity:
            stmt = stmt.where(AlarmEvent.severity == severity)
        return list(self.session.scalars(stmt).all())

    def get_active_by_signal(self, signal_id: str) -> list[AlarmEvent]:
        return list(
            self.session.scalars(
                select(AlarmEvent).where(
                    AlarmEvent.signal_id == signal_id,
                    AlarmEvent.state.in_(["active", "acknowledged"]),
                )
            ).all()
        )

    def update(self, event: AlarmEvent, data: dict) -> AlarmEvent:
        for key, value in data.items():
            if value is not None:
                setattr(event, key, value)
        self.session.commit()
        self.session.refresh(event)
        return event
