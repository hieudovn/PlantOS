# Phase 5 — Task 5-01: CDM Events + Stabilization (Gộp)

> **PM Decision:** Gộp Phase 5-01 với stabilization fixes. Code chạm cùng module — làm 1 lần.

## Scope

### A. CDM Event Contracts (Phase 5-01 gốc)
- 3 event models: StateEvent, DowntimeEvent, ProductionEvent
- CRUD API + EventPage UI

### B. Historian Hardening (SA Priority)
- Child table cache trong TDengineAdapter
- Batch INSERT (1 SQL cho nhiều points)
- `HISTORIAN_MODE` env var (tdengine | stub)
- Disable silent stub in non-dev mode
- Historian `/api/v1/historian/health` endpoint

### C. Side-Effect Refactor (SA Priority)
- `EventDispatcher` — internal pub/sub (in-process)
- Move WebSocket broadcast, alarm eval, calc eval ra khỏi router
- Measurement router chỉ: validate → historian write → dispatch

### D. UNS Governance (SA Priority)
- `UNSGenerator` service — auto-generate UNS path từ asset hierarchy
- `UNSValidator` — kiểm tra path format, chặn raw tag
- Enforce khi create signal: uns_path phải hợp lệ

## Files Summary

| Layer | Files | Purpose |
|---|---|---|
| **Events** | 6 CREATE | CDM event models + API |
| **Historian** | 2 MODIFY | Child cache + batch insert |
| **Core** | 3 CREATE | EventDispatcher + UNS service |
| **Config** | 1 MODIFY | HISTORIAN_MODE env var |
| **Frontend** | 1 CREATE | EventPage |
| **Routes** | 2 MODIFY | Include events + historian health |
| **Migration** | 1 CREATE | Event tables |
| **Total** | ~16 files | Tất cả trong 1 session |

## Key Code: EventDispatcher

```python
# backend/app/core/events.py
"""Internal event dispatcher — in-process pub/sub."""

import asyncio
from typing import Callable, Awaitable

_subscribers: dict[str, list[Callable]] = {}

def subscribe(event_type: str, handler: Callable):
    if event_type not in _subscribers:
        _subscribers[event_type] = []
    _subscribers[event_type].append(handler)

async def dispatch(event_type: str, data: dict):
    for handler in _subscribers.get(event_type, []):
        try:
            await handler(data)
        except Exception:
            pass  # Don't let one subscriber break others
```

Usage in measurement router:
```python
from app.core.events import dispatch
await dispatch("measurements.ingested", {"measurements": ws_data})
```

Subscribers registered at startup:
```python
subscribe("measurements.ingested", websocket_broadcaster)
subscribe("measurements.ingested", alarm_evaluator)
subscribe("measurements.ingested", calc_signal_evaluator)
```

## Key Code: UNS Validator

```python
# backend/app/modules/uns/validator.py
import re

UNS_PATTERN = re.compile(r'^[a-z0-9_-]+(/[a-z0-9_.-]+)*$')

def validate_uns_path(path: str) -> bool:
    """Validate UNS path format. Blocks raw tag patterns."""
    if not path or not UNS_PATTERN.match(path):
        return False
    # Block raw tag indicators
    blocked = ["plc:", "opc:", "ns=", "modbus:", "mqtt://"]
    for b in blocked:
        if b in path.lower():
            return False
    return True

def generate_uns_path(enterprise: str, plant_id: str, area_id: str, asset_id: str, signal_name: str) -> str:
    return f"{enterprise}/{plant_id}/{area_id}/{asset_id}/{signal_name}".lower()
```

## Key Code: TDengine Batch + Cache

```python
class TDengineHistorianAdapter:
    def __init__(self):
        self._child_tables: set[str] = set()  # Cache known child tables

    async def write_measurements(self, measurements):
        # Group by signal_id, ensure child tables exist (cached)
        groups = {}
        for m in measurements:
            safe = self._safe_name(m.signal_id)
            if safe not in self._child_tables:
                await self._ensure_child_table(m.signal_id)
                self._child_tables.add(safe)
            groups.setdefault(safe, []).append(m)

        # Batch INSERT: multiple VALUES in one SQL
        for safe_name, batch in groups.items():
            values = []
            for m in batch:
                ts = m.timestamp.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                val = "NULL" if m.value is None else str(m.value)
                values.append(f"('{ts}', {val}, '{m.quality.value}', '{m.source}')")

            sql = f"INSERT INTO d_{safe_name} VALUES {', '.join(values)}"
            self._cursor.execute(sql)
```

## Constraints

- [x] EventDispatcher in-process (không Kafka/Celery)
- [x] HISTORIAN_MODE=tdengine → fail if not available (non-dev)
- [x] HISTORIAN_MODE=stub → allowed in dev only
- [x] UNS validator blocks raw tag patterns
- [x] All existing tests must still pass (44)
