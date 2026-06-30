# Phase 4 — Task 4-01: Alarm Rule Engine

> **Designer:** DeepSeek V4 Pro | **Date:** 2026-06-30

## Context

Xây dựng Alarm Rule Engine — form-based, governed, template-driven. Không Node-RED.

Core: threshold rule → evaluate against measurement stream → create alarm → show in UI.

## Architecture

```
Measurement (WebSocket/ingest)
        │
        ▼
Rule Evaluator ──→ PostgreSQL (rule definitions)
        │
        ▼
Alarm State Machine
        │
        ▼
Alarm List API ──→ Frontend Alarm Page (🚧 → real)
```

## Implementation Checklist

- [ ] CREATE `backend/app/modules/alarms/models.py` — Rule + Alarm SQLAlchemy models
- [ ] CREATE `backend/app/modules/alarms/schemas.py` — Pydantic schemas
- [ ] CREATE `backend/app/modules/alarms/repository.py` — data access
- [ ] CREATE `backend/app/modules/alarms/service.py` — rule evaluator + alarm state machine
- [ ] CREATE `backend/app/modules/alarms/router.py` — CRUD rules + list alarms
- [ ] MODIFY `backend/app/modules/alarms/__init__.py` — exports
- [ ] MODIFY `backend/app/api/v1.py` — include alarms router
- [ ] MODIFY `backend/app/modules/measurements/router.py` — trigger rule evaluation after ingest
- [ ] MODIFY `backend/app/db/base.py` — import alarm models (for Alembic)
- [ ] CREATE `backend/migrations/versions/002_alarm_tables.py` — new migration
- [ ] MODIFY `frontend/src/routes/index.tsx` — replace Alarm 🚧
- [ ] CREATE `frontend/src/features/alarms/AlarmPage.tsx` — alarm table

## Detailed Instructions

### 1. `backend/app/modules/alarms/models.py`

```python
"""Alarm Rule Engine — SQLAlchemy models."""

import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Text, DateTime, ForeignKey, Boolean, Integer, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

def _utcnow(): return datetime.now(timezone.utc)
def _new_uuid(): return uuid.uuid4()


class AlarmRule(Base):
    __tablename__ = "alarm_rules"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=_new_uuid)
    rule_id: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    trigger_type: Mapped[str] = mapped_column(String(32), default="threshold")  # threshold | rate_of_change | state_change
    signal_id: Mapped[str] = mapped_column(String(256), nullable=False)
    asset_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    condition: Mapped[str] = mapped_column(String(8), default=">")  # > < >= <= == !=
    threshold: Mapped[float] = mapped_column(Float, nullable=False)
    hysteresis: Mapped[float] = mapped_column(Float, default=0.5)
    delay_seconds: Mapped[int] = mapped_column(Integer, default=5)
    severity: Mapped[str] = mapped_column(String(32), default="medium")  # low medium high critical
    message_template: Mapped[str | None] = mapped_column(Text, nullable=True)
    auto_clear: Mapped[bool] = mapped_column(Boolean, default=True)
    clear_threshold: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="active")  # active | inactive | draft
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    alarms: Mapped[list["AlarmEvent"]] = relationship("AlarmEvent", back_populates="rule", cascade="all, delete-orphan")


class AlarmEvent(Base):
    __tablename__ = "alarm_events"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=_new_uuid)
    alarm_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    rule_id_fk: Mapped[uuid.UUID] = mapped_column(ForeignKey("alarm_rules.id"), nullable=False)
    asset_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    signal_id: Mapped[str] = mapped_column(String(256), nullable=False)
    severity: Mapped[str] = mapped_column(String(32), default="medium")
    state: Mapped[str] = mapped_column(String(32), default="active")  # active | acknowledged | cleared
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    trigger_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cleared_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    rule: Mapped["AlarmRule"] = relationship("AlarmRule", back_populates="alarms")
```

### 2-4. Schemas + Repository + Service

Tạo theo 4-layer pattern giống Task 6-7. Tóm tắt:

**Schemas:** `AlarmRuleCreate`, `AlarmRuleResponse`, `AlarmEventResponse`
**Repository:** `AlarmRuleRepository`, `AlarmEventRepository` (CRUD pattern)
**Service:** `AlarmRuleService` (CRUD) + `AlarmEvaluator` (evaluate threshold rules against measurements, manage alarm state transitions: active → acknowledged → cleared)

### 5. `backend/app/modules/alarms/router.py`

```python
# CRUD for alarm rules
POST   /api/v1/alarm-rules
GET    /api/v1/alarm-rules
GET    /api/v1/alarm-rules/{rule_id}
PATCH  /api/v1/alarm-rules/{rule_id}
DELETE /api/v1/alarm-rules/{rule_id}

# Alarm events
GET    /api/v1/alarms                    ← list + filter by state/severity/asset
PATCH  /api/v1/alarms/{alarm_id}/ack     ← acknowledge
```

### 6. Trigger Evaluation After Ingest

Trong `measurements/router.py`, sau khi ingest:

```python
from app.modules.alarms.service import AlarmEvaluator
# After ingest success:
if result.accepted > 0:
    evaluator = AlarmEvaluator()
    await evaluator.evaluate(ws_data)  # ws_data: list of {"signal_id","value","quality","timestamp"}
```

### 7. `frontend/src/features/alarms/AlarmPage.tsx`

```tsx
// Fetch alarms from GET /api/v1/alarms
// Table: Alarm ID, Asset, Signal, Severity, State, Message, Time
// Filter by state (active/acknowledged/cleared)
// Acknowledge button per row
// Severity color: low=blue, medium=yellow, high=orange, critical=red
```

### 8. Migration

```bash
cd backend && alembic revision --autogenerate -m "alarm_tables"
```

## Constraints

- [x] Rules chỉ bind đến signal_id (CDM), không raw tag
- [x] Alarm state machine: active → acknowledged → cleared
- [x] Rule evaluation trigger after measurement ingest
- [x] Auto-clear: nếu value < clear_threshold, tự clear alarm
- [x] Hysteresis: tránh alarm flip-flop (12.0 trigger, 11.5 clear)

## Validation

```bash
# 1. Run migration
cd backend && alembic upgrade head

# 2. Create rule via API
curl -X POST http://localhost:8000/api/v1/alarm-rules -H "Content-Type: application/json" -d '{
  "rule_id":"pump-high-pressure","name":"Pump High Pressure",
  "signal_id":"PUMP-101.discharge_pressure","condition":">",
  "threshold":12.0,"severity":"high","message_template":"Pressure: {{value}} bar"
}'

# 3. Run simulator → trigger alarm
python edge/simulator/simulator.py --scenario pump_high_pressure --duration 30

# 4. Check alarms
curl http://localhost:8000/api/v1/alarms

# 5. Open alarm page
open http://localhost:5173/alarms
```

## Files Summary

| # | File | Action |
|---|------|--------|
| 1 | `backend/app/modules/alarms/models.py` | CREATE |
| 2 | `backend/app/modules/alarms/schemas.py` | CREATE |
| 3 | `backend/app/modules/alarms/repository.py` | CREATE |
| 4 | `backend/app/modules/alarms/service.py` | CREATE |
| 5 | `backend/app/modules/alarms/router.py` | CREATE |
| 6 | `backend/app/modules/alarms/__init__.py` | MODIFY |
| 7 | `backend/app/api/v1.py` | MODIFY |
| 8 | `backend/app/modules/measurements/router.py` | MODIFY |
| 9 | `backend/migrations/versions/002_alarm_tables.py` | CREATE |
| 10 | `frontend/src/routes/index.tsx` | MODIFY |
| 11 | `frontend/src/features/alarms/AlarmPage.tsx` | CREATE |
