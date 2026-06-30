# Phase 1 — Task 7: Signal Registry API

> **Designer:** DeepSeek V4 Pro | **Date:** 2026-06-30
> **Coder:** DeepSeek V4 Flash | **Reviewer:** DeepSeek V4 Pro
> **Status:** READY FOR IMPLEMENTATION

## Context

Implement Signal Registry CRUD API — theo 4-layer pattern đã thiết lập từ Task 6. Signal reference Asset qua `asset_id` business key, giống cách Area reference Plant.

API contract theo `docs/14-api-contract-mvp.md` §5. Pattern theo `backend/app/modules/assets/` (router → service → repository → model).

## Plan Reference

- `docs/14-api-contract-mvp.md` §5 — Signal API contract
- `docs/13-backend-service-design.md` §4 — Signal module responsibilities
- `docs/20-data-model.md` §3 — Signal entity fields
- `backend/app/modules/signals/models.py` — SQLAlchemy model (đã có từ Task 4)
- `backend/app/modules/assets/repository.py` — AssetRepository pattern để tham khảo

## Implementation Checklist

- [ ] CREATE `backend/app/modules/signals/schemas.py` — SignalCreate, SignalUpdate, SignalResponse
- [ ] CREATE `backend/app/modules/signals/repository.py` — SignalRepository
- [ ] CREATE `backend/app/modules/signals/service.py` — SignalService
- [ ] CREATE `backend/app/modules/signals/router.py` — 4 route handlers
- [ ] MODIFY `backend/app/modules/signals/__init__.py` — export router
- [ ] MODIFY `backend/app/api/v1.py` — include signals router
- [ ] CREATE `backend/tests/test_signal_api.py` — CRUD + filter tests

## API Endpoints

```text
POST   /api/v1/signals                     ← create signal
GET    /api/v1/signals                     ← list (?asset_id, ?signal_type, ?data_type)
GET    /api/v1/signals/{signal_id}         ← get detail
PATCH  /api/v1/signals/{signal_id}         ← update
```

## Exact Files to Create/Modify

| # | File Path | Action |
|---|-----------|--------|
| 1 | `backend/app/modules/signals/schemas.py` | CREATE |
| 2 | `backend/app/modules/signals/repository.py` | CREATE |
| 3 | `backend/app/modules/signals/service.py` | CREATE |
| 4 | `backend/app/modules/signals/router.py` | CREATE |
| 5 | `backend/app/modules/signals/__init__.py` | MODIFY |
| 6 | `backend/app/api/v1.py` | MODIFY |
| 7 | `backend/tests/test_signal_api.py` | CREATE |

## Detailed Instructions

### 1. `backend/app/modules/signals/schemas.py`

```python
"""Signal Registry — Pydantic request/response schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class SourceInfo(BaseModel):
    """Source reference — separates semantic signal from raw protocol."""
    source_type: str = "simulator"
    source_ref: Optional[str] = None


class SignalCreate(BaseModel):
    signal_id: str = Field(..., max_length=256, examples=["PUMP-101.discharge_pressure"])
    asset_id: str = Field(..., max_length=128)  # business key
    signal_name: str = Field(..., max_length=128)
    display_name: Optional[str] = None
    signal_type: str = "measurement"
    data_type: str = "float"
    engineering_unit: Optional[str] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    uns_path: Optional[str] = None
    source: Optional[SourceInfo] = None
    quality_policy: str = "GOOD"


class SignalUpdate(BaseModel):
    display_name: Optional[str] = None
    signal_type: Optional[str] = None
    engineering_unit: Optional[str] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    uns_path: Optional[str] = None
    source: Optional[SourceInfo] = None
    quality_policy: Optional[str] = None


class SignalResponse(BaseModel):
    signal_id: str
    asset_id: str
    signal_name: str
    display_name: Optional[str] = None
    signal_type: str
    data_type: str
    engineering_unit: Optional[str] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    uns_path: Optional[str] = None
    source: Optional[SourceInfo] = None
    quality_policy: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
```

### 2. `backend/app/modules/signals/repository.py`

```python
"""Signal Registry — SQLAlchemy repository layer."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.assets.models import Asset
from app.modules.signals.models import Signal


class SignalRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, signal: Signal) -> Signal:
        self.session.add(signal)
        self.session.commit()
        self.session.refresh(signal)
        return signal

    def get_by_id(self, signal_id: str) -> Signal | None:
        return self.session.scalar(
            select(Signal).where(Signal.signal_id == signal_id)
        )

    def list_all(
        self,
        asset_id: str | None = None,
        signal_type: str | None = None,
        data_type: str | None = None,
    ) -> list[Signal]:
        stmt = select(Signal)
        if asset_id:
            stmt = stmt.join(Asset).where(Asset.asset_id == asset_id)
        if signal_type:
            stmt = stmt.where(Signal.signal_type == signal_type)
        if data_type:
            stmt = stmt.where(Signal.data_type == data_type)
        return list(self.session.scalars(stmt).all())

    def update(self, signal: Signal, data: dict) -> Signal:
        for key, value in data.items():
            if value is not None:
                setattr(signal, key, value)
        self.session.commit()
        self.session.refresh(signal)
        return signal
```

### 3. `backend/app/modules/signals/service.py`

```python
"""Signal Registry — Service layer."""

from app.db import get_session
from app.modules.assets.models import Asset
from app.modules.assets.repository import AssetRepository
from app.modules.signals.models import Signal
from app.modules.signals.repository import SignalRepository
from app.modules.signals.schemas import (
    SignalCreate,
    SignalUpdate,
    SignalResponse,
    SourceInfo,
)


def _signal_to_response(signal: Signal) -> SignalResponse:
    source = None
    if signal.source_type or signal.source_ref:
        source = SourceInfo(
            source_type=signal.source_type,
            source_ref=signal.source_ref,
        )

    return SignalResponse(
        signal_id=signal.signal_id,
        asset_id=signal.asset.asset_id,
        signal_name=signal.signal_name,
        display_name=signal.display_name,
        signal_type=signal.signal_type,
        data_type=signal.data_type,
        engineering_unit=signal.engineering_unit,
        min_value=signal.min_value,
        max_value=signal.max_value,
        uns_path=signal.uns_path,
        source=source,
        quality_policy=signal.quality_policy,
        created_at=signal.created_at,
        updated_at=signal.updated_at,
    )


class SignalService:
    def create_signal(self, data: SignalCreate) -> SignalResponse:
        with get_session() as session:
            signal_repo = SignalRepository(session)
            if signal_repo.get_by_id(data.signal_id):
                raise ValueError(f"Signal '{data.signal_id}' already exists")

            # Resolve asset
            asset_repo = AssetRepository(session)
            asset = asset_repo.get_by_id(data.asset_id)
            if not asset:
                raise ValueError(f"Asset '{data.asset_id}' not found")

            source_type = data.source.source_type if data.source else "simulator"
            source_ref = data.source.source_ref if data.source else None

            signal = Signal(
                signal_id=data.signal_id,
                asset_id_fk=asset.id,
                signal_name=data.signal_name,
                display_name=data.display_name,
                signal_type=data.signal_type,
                data_type=data.data_type,
                engineering_unit=data.engineering_unit,
                min_value=data.min_value,
                max_value=data.max_value,
                uns_path=data.uns_path,
                source_type=source_type,
                source_ref=source_ref,
                quality_policy=data.quality_policy,
            )
            signal = signal_repo.create(signal)
            return _signal_to_response(signal)

    def get_signal(self, signal_id: str) -> SignalResponse:
        with get_session() as session:
            repo = SignalRepository(session)
            signal = repo.get_by_id(signal_id)
            if not signal:
                raise ValueError(f"Signal '{signal_id}' not found")
            return _signal_to_response(signal)

    def list_signals(
        self,
        asset_id: str | None = None,
        signal_type: str | None = None,
        data_type: str | None = None,
    ) -> list[SignalResponse]:
        with get_session() as session:
            repo = SignalRepository(session)
            signals = repo.list_all(asset_id, signal_type, data_type)
            return [_signal_to_response(s) for s in signals]

    def update_signal(self, signal_id: str, data: SignalUpdate) -> SignalResponse:
        with get_session() as session:
            repo = SignalRepository(session)
            signal = repo.get_by_id(signal_id)
            if not signal:
                raise ValueError(f"Signal '{signal_id}' not found")

            update_data = data.model_dump(exclude_unset=True)

            # Flatten source object
            if "source" in update_data:
                src = update_data.pop("source")
                if src:
                    update_data["source_type"] = src.source_type
                    update_data["source_ref"] = src.source_ref
                else:
                    update_data["source_type"] = "simulator"
                    update_data["source_ref"] = None

            signal = repo.update(signal, update_data)
            return _signal_to_response(signal)
```

### 4. `backend/app/modules/signals/router.py`

```python
"""Signal Registry — FastAPI router."""

from fastapi import APIRouter, HTTPException, Query

from app.modules.signals.schemas import (
    SignalCreate,
    SignalUpdate,
    SignalResponse,
)
from app.modules.signals.service import SignalService

router = APIRouter()
signal_service = SignalService()


@router.post("/signals", response_model=SignalResponse, status_code=201)
def create_signal(data: SignalCreate):
    try:
        return signal_service.create_signal(data)
    except ValueError as e:
        raise HTTPException(
            status_code=409 if "already" in str(e) else 404, detail=str(e)
        )


@router.get("/signals", response_model=list[SignalResponse])
def list_signals(
    asset_id: str | None = Query(None),
    signal_type: str | None = Query(None),
    data_type: str | None = Query(None),
):
    return signal_service.list_signals(asset_id, signal_type, data_type)


@router.get("/signals/{signal_id}", response_model=SignalResponse)
def get_signal(signal_id: str):
    try:
        return signal_service.get_signal(signal_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.patch("/signals/{signal_id}", response_model=SignalResponse)
def update_signal(signal_id: str, data: SignalUpdate):
    try:
        return signal_service.update_signal(signal_id, data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
```

### 5. `backend/app/modules/signals/__init__.py`

```python
from app.modules.signals.models import Signal  # noqa: F401
from app.modules.signals.router import router  # noqa: F401
```

### 6. `backend/app/api/v1.py` — Add signals router

```python
"""API v1 router — aggregates all module routers."""

from fastapi import APIRouter

from app.modules.assets.router import router as assets_router
from app.modules.signals.router import router as signals_router

router = APIRouter(prefix="/api/v1")
router.include_router(assets_router, tags=["Assets"])
router.include_router(signals_router, tags=["Signals"])
```

### 7. `backend/tests/test_signal_api.py`

```python
"""Integration tests for Signal Registry API."""

import os
import tempfile

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine

import app.modules as _modules  # noqa: F401

from app.main import app as _app
from app.db.base import Base


@pytest.fixture
def test_db_path():
    f = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    f.close()
    yield f.name
    os.unlink(f.name)


@pytest.fixture
def test_engine(test_db_path):
    engine = create_engine(
        f"sqlite:///{test_db_path}",
        echo=False,
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture(autouse=True)
def setup_db(test_engine, monkeypatch):
    from sqlalchemy.orm import sessionmaker
    TestSession = sessionmaker(bind=test_engine, expire_on_commit=False)
    import app.db.base as db_base
    monkeypatch.setattr(db_base, "_SessionLocal", TestSession)
    for table in reversed(Base.metadata.sorted_tables):
        with test_engine.connect() as conn:
            conn.execute(table.delete())
            conn.commit()


@pytest.fixture
async def client():
    transport = ASGITransport(app=_app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.fixture
async def setup_asset(client):
    """Create Plant + Area + Asset prerequisites."""
    await client.post("/api/v1/plants", json={"plant_id": "DEMO-PLANT", "name": "DP"})
    await client.post("/api/v1/areas", json={
        "area_id": "PROCESS-AREA", "plant_id": "DEMO-PLANT", "name": "PA",
    })
    await client.post("/api/v1/assets", json={
        "asset_id": "PUMP-101", "name": "Pump", "asset_type": "pump",
    })


# ---- Signal Tests ----

@pytest.mark.asyncio
async def test_create_signal(client, setup_asset):
    resp = await client.post("/api/v1/signals", json={
        "signal_id": "PUMP-101.discharge_pressure",
        "asset_id": "PUMP-101",
        "signal_name": "discharge_pressure",
        "display_name": "Discharge Pressure",
        "engineering_unit": "bar",
        "source": {"source_type": "simulator", "source_ref": "sim://pump-101/pressure"},
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["signal_id"] == "PUMP-101.discharge_pressure"
    assert data["asset_id"] == "PUMP-101"
    assert data["engineering_unit"] == "bar"
    assert data["source"]["source_type"] == "simulator"


@pytest.mark.asyncio
async def test_create_signal_asset_not_found(client):
    resp = await client.post("/api/v1/signals", json={
        "signal_id": "X.signal", "asset_id": "NOEXIST", "signal_name": "x",
    })
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_create_signal_duplicate(client, setup_asset):
    await client.post("/api/v1/signals", json={
        "signal_id": "PUMP-101.pressure", "asset_id": "PUMP-101", "signal_name": "p",
    })
    resp = await client.post("/api/v1/signals", json={
        "signal_id": "PUMP-101.pressure", "asset_id": "PUMP-101", "signal_name": "p2",
    })
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_get_signal(client, setup_asset):
    await client.post("/api/v1/signals", json={
        "signal_id": "PUMP-101.pressure", "asset_id": "PUMP-101", "signal_name": "p",
    })
    resp = await client.get("/api/v1/signals/PUMP-101.pressure")
    assert resp.status_code == 200
    assert resp.json()["signal_name"] == "p"


@pytest.mark.asyncio
async def test_get_signal_not_found(client):
    resp = await client.get("/api/v1/signals/NOEXIST.signal")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_list_signals(client, setup_asset):
    await client.post("/api/v1/signals", json={
        "signal_id": "PUMP-101.pressure", "asset_id": "PUMP-101", "signal_name": "p",
    })
    await client.post("/api/v1/signals", json={
        "signal_id": "PUMP-101.flow", "asset_id": "PUMP-101", "signal_name": "f",
    })
    resp = await client.get("/api/v1/signals")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


@pytest.mark.asyncio
async def test_list_signals_filter_asset(client, setup_asset):
    # Create second asset + signal
    await client.post("/api/v1/assets", json={
        "asset_id": "MOTOR-101", "name": "Motor", "asset_type": "motor",
    })
    await client.post("/api/v1/signals", json={
        "signal_id": "PUMP-101.pressure", "asset_id": "PUMP-101", "signal_name": "p",
    })
    await client.post("/api/v1/signals", json={
        "signal_id": "MOTOR-101.current", "asset_id": "MOTOR-101", "signal_name": "c",
    })

    resp = await client.get("/api/v1/signals?asset_id=PUMP-101")
    assert resp.status_code == 200
    assert len(resp.json()) == 1
    assert resp.json()[0]["signal_id"] == "PUMP-101.pressure"


@pytest.mark.asyncio
async def test_update_signal(client, setup_asset):
    await client.post("/api/v1/signals", json={
        "signal_id": "PUMP-101.pressure", "asset_id": "PUMP-101", "signal_name": "p",
    })
    resp = await client.patch("/api/v1/signals/PUMP-101.pressure", json={
        "display_name": "Updated Pressure",
        "engineering_unit": "kPa",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["display_name"] == "Updated Pressure"
    assert data["engineering_unit"] == "kPa"
    assert data["signal_name"] == "p"  # unchanged
```

## Constraints

- [x] 4-layer pattern: Router → Service → Repository → Model
- [x] `asset_id` là business key string trong API → Service resolve sang UUID FK
- [x] `source` là nested object trong API → flat `source_type`/`source_ref` trong DB
- [x] Không UNS/CDM bypass — Signal tách biệt semantic `signal_id` và raw `source_ref`
- [x] Test dùng SQLite in-memory (temp file, giống Task 6)

## Validation

```bash
cd backend
python -m pytest tests/ -v
```
Expected: ~37 tests passed (29 cũ + 8 mới)

## Expected Output Format

```
1. Files created/modified: [list 7 files]
2. Test results: XX/XX PASSED
3. 4-layer pattern confirmed: Router → Service → Repository → Model ✅
4. Issues / Deviations: [list]
5. Confirmation:
   - [x] API contract matches docs/14-api-contract-mvp.md §5
   - [x] No constitution rule violated
   - [x] source nested object → flat DB mapping correct
```
