"""Alarm Rule Engine — Service + Evaluator."""

import uuid
import re
from datetime import datetime, timezone
from string import Template

from app.db import get_session
from app.modules.alarms.models import AlarmRule, AlarmEvent
from app.modules.alarms.repository import AlarmRuleRepository, AlarmEventRepository


class AlarmRuleService:
    def _invalidate_cache(self):
        """Invalidate the AlarmEvaluator's rule cache so changes take effect."""
        AlarmEvaluator()._invalidate_cache()

    def create_rule(self, data) -> AlarmRule:
        with get_session() as session:
            repo = AlarmRuleRepository(session)
            if repo.get_by_id(data.rule_id):
                raise ValueError(f"Rule '{data.rule_id}' already exists")
            rule = AlarmRule(
                rule_id=data.rule_id,
                name=data.name,
                description=data.description,
                trigger_type=data.trigger_type,
                signal_id=data.signal_id,
                asset_id=data.asset_id,
                condition=data.condition,
                threshold=data.threshold,
                hysteresis=data.hysteresis,
                delay_seconds=data.delay_seconds,
                severity=data.severity,
                message_template=data.message_template,
                auto_clear=data.auto_clear,
                clear_threshold=data.clear_threshold,
                status=data.status,
            )
            rule = repo.create(rule)
            self._invalidate_cache()
            return rule

    def get_rule(self, rule_id: str) -> AlarmRule | None:
        with get_session() as session:
            return AlarmRuleRepository(session).get_by_id(rule_id)

    def list_rules(self, status: str | None = None) -> list[AlarmRule]:
        with get_session() as session:
            return AlarmRuleRepository(session).list_all(status)

    def update_rule(self, rule_id: str, data) -> AlarmRule:
        with get_session() as session:
            repo = AlarmRuleRepository(session)
            rule = repo.get_by_id(rule_id)
            if not rule:
                raise ValueError(f"Rule '{rule_id}' not found")
            update_data = data.model_dump(exclude_unset=True)
            result = repo.update(rule, update_data)
            self._invalidate_cache()
            return result

    def delete_rule(self, rule_id: str):
        with get_session() as session:
            repo = AlarmRuleRepository(session)
            rule = repo.get_by_id(rule_id)
            if not rule:
                raise ValueError(f"Rule '{rule_id}' not found")
            repo.delete(rule)
            self._invalidate_cache()


class AlarmEvaluator:
    """Evaluate threshold rules against measurements and manage alarm state."""

    def __init__(self):
        self._rule_cache: list[AlarmRule] | None = None

    def _load_active_rules(self) -> list[AlarmRule]:
        if self._rule_cache is None:
            with get_session() as session:
                repo = AlarmRuleRepository(session)
                self._rule_cache = repo.list_all(status="active")
        return self._rule_cache

    def _invalidate_cache(self):
        self._rule_cache = None

    def _format_message(self, template: str | None, value: float, rule: AlarmRule) -> str:
        if not template:
            return f"{rule.name} triggered: {value} {rule.condition} {rule.threshold}"
        return template.replace("{{value}}", str(value)).replace("{{threshold}}", str(rule.threshold))

    async def evaluate(self, measurements: list[dict]):
        """Evaluate batch of measurements against active rules."""
        from app.core.events import dispatch

        rules = self._load_active_rules()
        if not rules:
            return

        for m in measurements:
            signal_id = m.get("signal_id", m.get("sid"))
            value = m.get("value")
            if value is None or not isinstance(value, (int, float)):
                continue

            for rule in rules:
                if rule.signal_id != signal_id:
                    continue

                triggered = self._check_condition(value, rule.condition, rule.threshold)

                with get_session() as session:
                    event_repo = AlarmEventRepository(session)
                    active_alarms = event_repo.get_active_by_signal(signal_id)

                    if triggered:
                        existing = [a for a in active_alarms if a.rule_id_fk == rule.id]
                        if not existing:
                            alarm_id = str(uuid.uuid4())[:8]
                            message = self._format_message(rule.message_template, value, rule)
                            event = AlarmEvent(
                                alarm_id=alarm_id,
                                rule_id_fk=rule.id,
                                asset_id=rule.asset_id,
                                signal_id=signal_id,
                                severity=rule.severity,
                                state="active",
                                message=message,
                                trigger_value=value,
                            )
                            event_repo.create(event)

                            # Compute correlation_id from the created alarm's timestamp
                            # This ensures AlarmRaised and AlarmCleared share the same ID
                            alarm_code = getattr(rule, "alarm_code", rule.name)
                            correlation_id = (
                                f"alarm-{rule.asset_id}-{alarm_code}-"
                                f"{event.started_at.strftime('%Y%m%dT%H%M%SZ')}"
                            )

                            # Dispatch AlarmRaised event
                            rule_data = {
                                "name": rule.name,
                                "alarm_code": alarm_code,
                                "severity": rule.severity,
                                "threshold": rule.threshold,
                                "condition": rule.condition,
                            }
                            alarm_data = {
                                "alarm_id": alarm_id,
                                "asset_id": rule.asset_id,
                                "signal_id": signal_id,
                                "severity": rule.severity,
                                "state": "active",
                                "message": message,
                                "trigger_value": value,
                            }
                            await dispatch("alarm.raised", {
                                "alarm": alarm_data,
                                "rule": rule_data,
                                "correlation_id": correlation_id,
                            })

                    elif rule.auto_clear and rule.clear_threshold is not None:
                        if (rule.condition in (">", ">=") and value <= rule.clear_threshold) or \
                           (rule.condition in ("<", "<=") and value >= rule.clear_threshold):
                            for a in active_alarms:
                                if a.rule_id_fk == rule.id:
                                    event_repo.update(a, {
                                        "state": "cleared",
                                        "cleared_at": datetime.now(timezone.utc),
                                    })

                                    # Dispatch AlarmCleared event
                                    # Use started_at for consistency with AlarmRaised correlation_id
                                    alarm_code = getattr(rule, "alarm_code", rule.name)
                                    correlation_id = (
                                        f"alarm-{rule.asset_id}-{alarm_code}-"
                                        f"{a.started_at.strftime('%Y%m%dT%H%M%SZ')}"
                                    )
                                    rule_data = {
                                        "name": rule.name,
                                        "alarm_code": alarm_code,
                                        "severity": rule.severity,
                                    }
                                    alarm_data = {
                                        "alarm_id": a.alarm_id,
                                        "asset_id": rule.asset_id,
                                        "signal_id": signal_id,
                                        "severity": rule.severity,
                                        "state": "cleared",
                                    }
                                    await dispatch("alarm.cleared", {
                                        "alarm": alarm_data,
                                        "rule": rule_data,
                                        "correlation_id": correlation_id,
                                    })

    def _check_condition(self, value: float, condition: str, threshold: float) -> bool:
        if condition == ">":
            return value > threshold
        elif condition == ">=":
            return value >= threshold
        elif condition == "<":
            return value < threshold
        elif condition == "<=":
            return value <= threshold
        elif condition == "==":
            return value == threshold
        elif condition == "!=":
            return value != threshold
        return False


def list_alarms(state: str | None = None, severity: str | None = None, limit: int = 100) -> list[AlarmEvent]:
    with get_session() as session:
        repo = AlarmEventRepository(session)
        events = repo.list_all(state=state, severity=severity, limit=limit)
        return events


def acknowledge_alarm(alarm_id: str) -> AlarmEvent:
    with get_session() as session:
        repo = AlarmEventRepository(session)
        event = repo.get_by_id(alarm_id)
        if not event:
            raise ValueError(f"Alarm '{alarm_id}' not found")
        if event.state == "cleared":
            raise ValueError(f"Alarm '{alarm_id}' already cleared")
        return repo.update(event, {
            "state": "acknowledged",
            "acknowledged_at": datetime.now(timezone.utc),
        })
