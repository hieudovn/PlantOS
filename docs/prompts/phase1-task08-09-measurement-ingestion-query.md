# Phase 1 — Task 8-9: Measurement Ingestion + Query API (Gộp)

> **Designer:** DeepSeek V4 Pro | **Date:** 2026-06-30
> **Reason for merge:** Ingestion và Query cùng module `measurements`, dùng chung `HistorianInterface`. Gộp để test end-to-end (write → read) trong một lần.

## Context

Implement Measurement Ingestion + Current Value + History Query APIs. Đây là task đầu tiên **tích hợp HistorianInterface** (từ Task 5). Measurement API gọi `historian.write_measurements(batch)` — không biết TDengine.

API contract theo `docs/14-api-contract-mvp.md` §6.

## Plan Reference

- `docs/14-api-contract-mvp.md` §6 — Measurement API contract
- `docs/13-backend-service-design.md` §4 — Measurement module responsibilities
- `docs/15-storage-and-historian-design.md` §5-6 — Measurement schema
- `backend/app/modules/historian/interface.py` — HistorianInterface (đã có)
- `backend/app/modules/historian/stub_adapter.py` — StubHistorianAdapter (test)

## API Endpoints

```text
POST  /api/v1/measurements/ingest              ← batch ingest
GET   /api/v1/measurements/current?asset_id=X   ← latest values
GET   /api/v1/measurements/history?signal_id=X  ← time-series range
```

## Implementation Checklist

- [ ] CREATE `backend/app/modules/measurements/schemas.py` — IngestRequest, IngestResponse, CurrentQuery, HistoryQuery
- [ ] CREATE `backend/app/modules/measurements/service.py` — MeasurementService
- [ ] CREATE `backend/app/modules/measurements/router.py` — 3 routes
- [ ] MODIFY `backend/app/modules/measurements/__init__.py` — export router
- [ ] MODIFY `backend/app/api/v1.py` — include measurements router
- [ ] CREATE `backend/tests/test_measurement_api.py` — ingest + query tests

## Detailed Instructions

### 1. `backend/app/modules/measurements/schemas.py`

```python
"""Measurement — Pydantic request/response schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class MeasurementPoint(BaseModel):
    """Single measurement data point for ingestion."""
    timestamp: datetime
    signal_id: str
    value: float | bool
    quality: str = "GOOD"


class IngestRequest(BaseModel):
    """Batch measurement ingestion request — matches API contract."""
    source: str = "unknown"
    measurements: list[MeasurementPoint]


class IngestResponse(BaseModel):
    """Batch ingestion result."""
    accepted: int
    rejected: int
    errors: list[str] = Field(default_factory=list)


class CurrentValueResponse(BaseModel):
    """Current value for a single signal."""
    signal_id: str
    asset_id: Optional[str] = None
    timestamp: Optional[datetime] = None
    value: Optional[float | bool] = None
    quality: Optional[str] = None
    source: Optional[str] = None


class HistoryQueryParams(BaseModel):
    """Query parameters for historical data."""
    signal_id: str
    from_ts: datetime
    to_ts: datetime
    interval: Optional[str] = None  # e.g., "1m", "5m", "1h"


class HistoryResponse(BaseModel):
    """Historical data response."""
    signal_id: str
    data: list[CurrentValueResponse] = Field(default_factory=list)
```

### 2. `backend/app/modules/measurements/service.py`

```python
"""Measurement Service — ingestion + query via HistorianInterface."""

from app.db import get_session
from app.modules.historian.interface import HistorianInterface
from app.modules.historian.models import Measurement as HistorianMeasurement
from app.modules.historian.models import Quality as HistorianQuality
from app.modules.signals.repository import SignalRepository
from app.modules.assets.repository import AssetRepository
from app.modules.measurements.schemas import (
    IngestRequest,
    IngestResponse,
    CurrentValueResponse,
    HistoryQueryParams,
    HistoryResponse,
)


class MeasurementService:
    def __init__(self, historian: HistorianInterface):
        self.historian = historian

    async def ingest(self, data: IngestRequest) -> IngestResponse:
        """Validate signal_ids and write batch to historian."""
        # Validate all signal_ids exist
        with get_session() as session:
            signal_repo = SignalRepository(session)
            valid_ids = set()
            errors = []
            for m in data.measurements:
                signal = signal_repo.get_by_id(m.signal_id)
                if signal:
                    valid_ids.add(m.signal_id)
                else:
                    errors.append(f"Signal '{m.signal_id}' not found")

        # Convert to historian Measurement objects (only valid signals)
        historian_measurements = [
            HistorianMeasurement(
                timestamp=m.timestamp,
                signal_id=m.signal_id,
                value=m.value,
                quality=HistorianQuality(m.quality),
                source=data.source,
            )
            for m in data.measurements
            if m.signal_id in valid_ids
        ]

        # Write to historian
        result = await self.historian.write_measurements(historian_measurements)
        result.errors.extend(errors)
        result.rejected += len(errors)
        return IngestResponse(
            accepted=result.accepted,
            rejected=result.rejected,
            errors=result.errors,
        )

    async def get_current(self, asset_id: str | None = None, signal_id: str | None = None) -> list[CurrentValueResponse]:
        """Get current (latest) values. Filter by asset_id or signal_id."""
        # Resolve signal_ids
        signal_ids = []
        with get_session() as session:
            if signal_id:
                signal_ids = [signal_id]
            elif asset_id:
                asset_repo = AssetRepository(session)
                asset = asset_repo.get_by_id(asset_id)
                if not asset:
                    return []
                signal_ids = [s.signal_id for s in asset.signals]
            else:
                return []  # Must provide asset_id or signal_id

        # Query historian
        latest_map = await self.historian.query_latest(signal_ids)

        # Build response
        results = []
        for sid in signal_ids:
            m = latest_map.get(sid)
            with get_session() as session:
                signal_repo = SignalRepository(session)
                signal = signal_repo.get_by_id(sid)
                asset_id_val = signal.asset.asset_id if signal else None

            results.append(CurrentValueResponse(
                signal_id=sid,
                asset_id=asset_id_val,
                timestamp=m.timestamp if m else None,
                value=m.value if m else None,
                quality=m.quality.value if m and m.quality else None,
                source=m.source if m else None,
            ))
        return results

    async def get_history(self, params: HistoryQueryParams) -> HistoryResponse:
        """Get historical data for a signal."""
        measurements = await self.historian.query_history(
            signal_id=params.signal_id,
            from_ts=params.from_ts,
            to_ts=params.to_ts,
            interval=params.interval,
        )
        data = [
            CurrentValueResponse(
                signal_id=m.signal_id,
                timestamp=m.timestamp,
                value=m.value,
                quality=m.quality.value if m.quality else None,
                source=m.source,
            )
            for m in measurements
        ]
        return HistoryResponse(signal_id=params.signal_id, data=data)
```

### 3. `backend/app/modules/measurements/router.py`

```python
"""Measurement API — FastAPI router."""

from fastapi import APIRouter, HTTPException, Query, Depends

from app.modules.historian.interface import HistorianInterface
from app.modules.historian.stub_adapter import StubHistorianAdapter
from app.modules.measurements.schemas import (
    IngestRequest,
    IngestResponse,
    CurrentValueResponse,
    HistoryQueryParams,
    HistoryResponse,
)
from app.modules.measurements.service import MeasurementService


# Dependency — replace with TDengine adapter when running with Docker
def get_historian() -> HistorianInterface:
    """Provide a historian adapter instance.
    
    Tries TDengine first; falls back to Stub.
    Replace this with proper DI later.
    """
    try:
        from app.modules.historian.tdengine_adapter import TDengineHistorianAdapter
        return TDengineHistorianAdapter()
    except ImportError:
        return StubHistorianAdapter()


router = APIRouter()


@router.post("/measurements/ingest", response_model=IngestResponse)
async def ingest_measurements(data: IngestRequest, historian: HistorianInterface = Depends(get_historian)):
    service = MeasurementService(historian)
    return await service.ingest(data)


@router.get("/measurements/current", response_model=list[CurrentValueResponse])
async def get_current_values(
    asset_id: str | None = Query(None),
    signal_id: str | None = Query(None),
    historian: HistorianInterface = Depends(get_historian),
):
    if not asset_id and not signal_id:
        raise HTTPException(status_code=400, detail="Provide asset_id or signal_id")
    service = MeasurementService(historian)
    return await service.get_current(asset_id=asset_id, signal_id=signal_id)


@router.get("/measurements/history", response_model=HistoryResponse)
async def get_history(
    signal_id: str = Query(...),
    from_ts: str = Query(..., alias="from"),
    to_ts: str = Query(..., alias="to"),
    interval: str | None = Query(None),
    historian: HistorianInterface = Depends(get_historian),
):
    from datetime import datetime
    try:
        params = HistoryQueryParams(
            signal_id=signal_id,
            from_ts=datetime.fromisoformat(from_ts),
            to_ts=datetime.fromisoformat(to_ts),
            interval=interval,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid timestamp: {e}")
    service = MeasurementService(historian)
    return await service.get_history(params)
```

### 4-5. Module init + v1 router

`backend/app/modules/measurements/__init__.py`:
```python
from app.modules.measurements.router import router  # noqa: F401
```

`backend/app/api/v1.py` — add:
```python
from app.modules.measurements.router import router as measurements_router
router.include_router(measurements_router, tags=["Measurements"])
```

### 6. `backend/tests/test_measurement_api.py`

Viết test với StubHistorianAdapter (in-memory). Test:
- POST ingest batch → 201
- POST ingest with unknown signal_id → accepted=0, rejected=N, errors present
- GET current?asset_id=X → returns latest values
- GET current without params → 400
- GET history?signal_id=X&from=...&to=... → returns time-series
- GET history with invalid timestamp → 400

> Coder tự viết test code — pattern giống test_asset_api.py và test_signal_api.py. Dùng StubHistorianAdapter (không cần TDengine).

## Constraints

- [x] Measurement API gọi qua `HistorianInterface` — không biết TDengine
- [x] Validate signal_id tồn tại trước khi ghi (qua SignalRepository)
- [x] Batch ingest: signal không tồn tại → rejected, không crash
- [x] `current` API yêu cầu `asset_id` hoặc `signal_id`
- [x] `history` API yêu cầu `signal_id` + `from` + `to`

## Validation

```bash
cd backend
python -m pytest tests/ -v
```
Expected: ~44 tests passed (37 cũ + ~7 mới)

## Expected Output Format

Standard — như các task trước.
