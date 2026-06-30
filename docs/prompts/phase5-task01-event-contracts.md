# Phase 5 — Task 5-01: CDM Event Contracts

> **Designer:** DeepSeek V4 Pro | **Date:** 2026-06-30

## Context

PlantOS events must follow CDM — semantic operational events (equipment state change, downtime, production context), not raw tag events. MES và Virtual Factory sẽ consume các event này.

## CDM Event Types

```
Equipment State Event:
  asset_id: PUMP-101
  from_state: running
  to_state: stopped
  reason: "Operator stop"
  timestamp: 2026-06-30T14:00:00Z

Downtime Event:
  asset_id: PUMP-101
  start_time, end_time, duration_seconds
  category: planned | unplanned | idle
  reason: "Maintenance"

Production Event:
  asset_id: LINE-01
  order_id: "MO-2026-001"
  operation: "filling"
  quantity: 1000
  status: started | completed | paused
```

## Implementation Checklist

- [ ] CREATE `backend/app/modules/events/models.py` — SQLAlchemy models
- [ ] CREATE `backend/app/modules/events/schemas.py` — Pydantic
- [ ] CREATE `backend/app/modules/events/repository.py` — data access
- [ ] CREATE `backend/app/modules/events/service.py` — business logic
- [ ] CREATE `backend/app/modules/events/router.py` — API endpoints
- [ ] CREATE `backend/app/modules/events/__init__.py`
- [ ] MODIFY `backend/app/api/v1.py` — include events router
- [ ] CREATE `backend/migrations/versions/003_event_tables.py`
- [ ] MODIFY `frontend/src/routes/index.tsx` — add Events page placeholder
- [ ] CREATE `frontend/src/features/events/EventPage.tsx` — simple event table

## API Endpoints

```text
POST   /api/v1/events/state          ← record equipment state change
POST   /api/v1/events/downtime       ← record downtime event  
POST   /api/v1/events/production     ← record production event
GET    /api/v1/events                ← list events (?asset_id, ?type, ?from, ?to)
GET    /api/v1/events/{event_id}     ← event detail
```

## Models

```python
class EquipmentStateEvent(Base):
    __tablename__ = "equipment_state_events"
    id, event_id (UK), asset_id, from_state, to_state, reason, timestamp

class DowntimeEvent(Base):
    __tablename__ = "downtime_events"  
    id, event_id (UK), asset_id, start_time, end_time, duration_seconds, category, reason

class ProductionEvent(Base):
    __tablename__ = "production_events"
    id, event_id (UK), asset_id, order_id, operation, quantity, status, timestamp
```

## Schemas (Pydantic)

```python
class StateEventCreate(BaseModel):
    asset_id: str
    from_state: str
    to_state: str
    reason: str | None = None

class DowntimeEventCreate(BaseModel):
    asset_id: str
    start_time: datetime
    end_time: datetime | None = None
    category: str = "unplanned"
    reason: str | None = None

class ProductionEventCreate(BaseModel):
    asset_id: str
    order_id: str
    operation: str
    quantity: float | None = None
    status: str = "started"
```

## Frontend — EventPage.tsx

Simple event table với filters: type (state/downtime/production), asset_id. Replace "Coming in next phase" placeholder. Hiển thị timeline events giống alarm page nhưng không có ack/severity.

## Constraints

- [x] Events dùng asset_id (CDM), không raw tag
- [x] Mỗi event type có schema riêng (không generic event dump)
- [x] API response include event_id + timestamp + asset context
- [x] Migration có downgrade

## Validation

```bash
# 1. Migration
cd backend && alembic upgrade head

# 2. Create equipment state event
curl -X POST http://localhost:8000/api/v1/events/state -d '{
  "asset_id":"PUMP-101","from_state":"running","to_state":"stopped","reason":"test"
}'

# 3. Create downtime event
curl -X POST http://localhost:8000/api/v1/events/downtime -d '{
  "asset_id":"PUMP-101","category":"unplanned","reason":"Motor trip"
}'

# 4. List events
curl http://localhost:8000/api/v1/events?asset_id=PUMP-101

# 5. Open Events page
open http://localhost:5173/events
```

## Files Summary

| # | File | Action |
|---|------|--------|
| 1 | `backend/app/modules/events/models.py` | CREATE |
| 2 | `backend/app/modules/events/schemas.py` | CREATE |
| 3 | `backend/app/modules/events/repository.py` | CREATE |
| 4 | `backend/app/modules/events/service.py` | CREATE |
| 5 | `backend/app/modules/events/router.py` | CREATE |
| 6 | `backend/app/modules/events/__init__.py` | CREATE |
| 7 | `backend/app/api/v1.py` | MODIFY |
| 8 | `backend/migrations/versions/003_event_tables.py` | CREATE |
| 9 | `frontend/src/routes/index.tsx` | MODIFY |
| 10 | `frontend/src/features/events/EventPage.tsx` | CREATE |
