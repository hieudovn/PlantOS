# Phase 1 — Task 6: Asset Registry API

> **Designer:** DeepSeek V4 Pro | **Date:** 2026-06-30
> **Coder:** DeepSeek V4 Flash | **Reviewer:** DeepSeek V4 Pro
> **Status:** READY FOR IMPLEMENTATION

## Context

Implement Asset Registry CRUD API — đây là module API đầu tiên của PlantOS, thiết lập **4-layer pattern chuẩn** (Router → Service → Repository → Model) cho toàn bộ các module sau. Cần có Plant + Area endpoints tối thiểu để Asset có thể reference.

API contract theo `docs/14-api-contract-mvp.md` §4. Backend rules theo `docs/13-backend-service-design.md` §5: "API routes must call service layer, not database directly."

## Plan Reference

- `docs/14-api-contract-mvp.md` §2-4 — Base URL, common fields, Asset API contract
- `docs/13-backend-service-design.md` §4-7 — Module responsibilities, architecture rules, endpoints
- `docs/20-data-model.md` §3 — Core entities (Plant, Area, Asset)
- `backend/app/modules/assets/models.py` — SQLAlchemy models (đã có từ Task 4)
- `backend/app/db/base.py` — `get_session()` (đã có)

## Implementation Checklist

- [ ] CREATE `backend/app/api/v1.py` — v1 router aggregation
- [ ] MODIFY `backend/app/api/__init__.py` — re-export v1 router
- [ ] CREATE `backend/app/modules/assets/schemas.py` — Pydantic request/response
- [ ] CREATE `backend/app/modules/assets/repository.py` — SQLAlchemy data access
- [ ] CREATE `backend/app/modules/assets/service.py` — business logic + validation
- [ ] CREATE `backend/app/modules/assets/router.py` — FastAPI routes
- [ ] MODIFY `backend/app/modules/assets/__init__.py` — export router
- [ ] MODIFY `backend/app/main.py` — include v1 router
- [ ] CREATE `backend/tests/test_asset_api.py` — API integration tests

## API Endpoints to Implement

```text
POST   /api/v1/plants                      ← create plant
GET    /api/v1/plants                      ← list plants
GET    /api/v1/plants/{plant_id}           ← get plant

POST   /api/v1/areas                       ← create area (requires plant)
GET    /api/v1/areas                       ← list areas (optional ?plant_id filter)
GET    /api/v1/areas/{area_id}             ← get area

POST   /api/v1/assets                      ← create asset
GET    /api/v1/assets                      ← list assets (?plant_id, ?area_id, ?asset_type)
GET    /api/v1/assets/{asset_id}           ← get asset detail
PATCH  /api/v1/assets/{asset_id}           ← update asset
```

## Layer Architecture

```text
HTTP Request
    ↓
router.py      ← FastAPI route handler, parse params, return Response
    ↓
service.py     ← business logic, validation, orchestration
    ↓
repository.py  ← SQLAlchemy queries, DB access ONLY
    ↓
models.py      ← SQLAlchemy ORM models (đã có)
```

**Rule:** Router KHÔNG gọi repository trực tiếp. Router chỉ gọi service. Service gọi repository.

## Exact Files to Create/Modify

| # | File Path | Action | Content Summary |
|---|-----------|--------|-----------------|
| 1 | `backend/app/api/__init__.py` | MODIFY | Re-export v1 router |
| 2 | `backend/app/api/v1.py` | CREATE | APIRouter aggregation cho `/api/v1` |
| 3 | `backend/app/modules/assets/schemas.py` | CREATE | Pydantic models: PlantCreate/Response, AreaCreate/Response, AssetCreate/Update/Response |
| 4 | `backend/app/modules/assets/repository.py` | CREATE | PlantRepository, AreaRepository, AssetRepository |
| 5 | `backend/app/modules/assets/service.py` | CREATE | PlantService, AreaService, AssetService |
| 6 | `backend/app/modules/assets/router.py` | CREATE | 8 route handlers |
| 7 | `backend/app/modules/assets/__init__.py` | MODIFY | Export router |
| 8 | `backend/app/main.py` | MODIFY | Include v1 router |
| 9 | `backend/tests/test_asset_api.py` | CREATE | API integration tests via TestClient |

## Detailed Instructions

### 1. `backend/app/api/__init__.py` — Re-export

```python
from app.api.v1 import router as v1_router

__all__ = ["v1_router"]
```

### 2. `backend/app/api/v1.py` — V1 Router

```python
"""API v1 router — aggregates all module routers."""

from fastapi import APIRouter

from app.modules.assets.router import router as assets_router

router = APIRouter(prefix="/api/v1")
router.include_router(assets_router, tags=["Assets"])
```

> Các module router sau (signals, measurements, ...) sẽ được include tương tự.

### 3. `backend/app/modules/assets/schemas.py` — Pydantic Schemas

```python
"""Asset Registry — Pydantic request/response schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# ---- Plant ----

class PlantCreate(BaseModel):
    plant_id: str = Field(..., max_length=64, examples=["DEMO-PLANT"])
    name: str = Field(..., max_length=255)
    location: Optional[str] = None
    timezone: str = "UTC"
    status: str = "active"


class PlantResponse(BaseModel):
    plant_id: str
    name: str
    location: Optional[str] = None
    timezone: str
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ---- Area ----

class AreaCreate(BaseModel):
    area_id: str = Field(..., max_length=64, examples=["PROCESS-AREA"])
    plant_id: str = Field(..., max_length=64)
    name: str = Field(..., max_length=255)
    area_type: Optional[str] = None
    status: str = "active"


class AreaResponse(BaseModel):
    area_id: str
    plant_id: str
    name: str
    area_type: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ---- Asset ----

class Location(BaseModel):
    lat: float
    lng: float


class AssetCreate(BaseModel):
    asset_id: str = Field(..., max_length=128, examples=["PUMP-101"])
    asset_code: Optional[str] = None
    name: str = Field(..., max_length=255)
    asset_type: str = Field(..., max_length=64)
    plant_id: Optional[str] = None  # business key, resolved to Plant
    area_id: Optional[str] = None   # business key, resolved to Area
    parent_asset_id: Optional[str] = None  # business key, self-ref
    criticality: str = "medium"
    lifecycle_status: str = "active"
    location: Optional[Location] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None


class AssetUpdate(BaseModel):
    name: Optional[str] = None
    asset_type: Optional[str] = None
    area_id: Optional[str] = None
    parent_asset_id: Optional[str] = None
    criticality: Optional[str] = None
    lifecycle_status: Optional[str] = None
    location: Optional[Location] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None


class AssetResponse(BaseModel):
    asset_id: str
    asset_code: Optional[str] = None
    name: str
    asset_type: str
    plant_id: Optional[str] = None   # resolved from area→plant
    area_id: Optional[str] = None
    parent_asset_id: Optional[str] = None
    criticality: str
    lifecycle_status: str
    location: Optional[Location] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
```

### 4. `backend/app/modules/assets/repository.py` — Data Access

```python
"""Asset Registry — SQLAlchemy repository layer."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.assets.models import Plant, Area, Asset


class PlantRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, plant: Plant) -> Plant:
        self.session.add(plant)
        self.session.commit()
        self.session.refresh(plant)
        return plant

    def get_by_id(self, plant_id: str) -> Plant | None:
        return self.session.scalar(
            select(Plant).where(Plant.plant_id == plant_id)
        )

    def list_all(self) -> list[Plant]:
        return list(self.session.scalars(select(Plant)).all())


class AreaRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, area: Area) -> Area:
        self.session.add(area)
        self.session.commit()
        self.session.refresh(area)
        return area

    def get_by_id(self, area_id: str) -> Area | None:
        return self.session.scalar(
            select(Area).where(Area.area_id == area_id)
        )

    def list_by_plant(self, plant_id: str | None = None) -> list[Area]:
        stmt = select(Area)
        if plant_id:
            stmt = stmt.join(Plant).where(Plant.plant_id == plant_id)
        return list(self.session.scalars(stmt).all())


class AssetRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, asset: Asset) -> Asset:
        self.session.add(asset)
        self.session.commit()
        self.session.refresh(asset)
        return asset

    def get_by_id(self, asset_id: str) -> Asset | None:
        return self.session.scalar(
            select(Asset).where(Asset.asset_id == asset_id)
        )

    def list_all(
        self,
        plant_id: str | None = None,
        area_id: str | None = None,
        asset_type: str | None = None,
    ) -> list[Asset]:
        stmt = select(Asset)
        if area_id:
            stmt = stmt.join(Area).where(Area.area_id == area_id)
        if plant_id:
            stmt = stmt.join(Area).join(Plant).where(Plant.plant_id == plant_id)
        if asset_type:
            stmt = stmt.where(Asset.asset_type == asset_type)
        return list(self.session.scalars(stmt).all())

    def update(self, asset: Asset, data: dict) -> Asset:
        for key, value in data.items():
            if value is not None:
                setattr(asset, key, value)
        self.session.commit()
        self.session.refresh(asset)
        return asset
```

### 5. `backend/app/modules/assets/service.py` — Business Logic

```python
"""Asset Registry — Service layer (business logic + validation)."""

from app.db import get_session
from app.modules.assets.models import Plant, Area, Asset
from app.modules.assets.repository import PlantRepository, AreaRepository, AssetRepository
from app.modules.assets.schemas import (
    PlantCreate,
    PlantResponse,
    AreaCreate,
    AreaResponse,
    AssetCreate,
    AssetUpdate,
    AssetResponse,
    Location,
)


# ---- Helpers ----

def _plant_to_response(plant: Plant, area: Area | None = None) -> PlantResponse:
    return PlantResponse.model_validate(plant)


def _area_to_response(area: Area) -> AreaResponse:
    return AreaResponse(
        area_id=area.area_id,
        plant_id=area.plant.plant_id,
        name=area.name,
        area_type=area.area_type,
        status=area.status,
        created_at=area.created_at,
        updated_at=area.updated_at,
    )


def _asset_to_response(asset: Asset) -> AssetResponse:
    plant_id = None
    area_id = None
    if asset.area:
        area_id = asset.area.area_id
        if asset.area.plant:
            plant_id = asset.area.plant.plant_id

    location = None
    if asset.location_lat is not None and asset.location_lng is not None:
        location = Location(lat=asset.location_lat, lng=asset.location_lng)

    return AssetResponse(
        asset_id=asset.asset_id,
        asset_code=asset.asset_code,
        name=asset.name,
        asset_type=asset.asset_type,
        plant_id=plant_id,
        area_id=area_id,
        parent_asset_id=asset.parent.asset_id if asset.parent else None,
        criticality=asset.criticality,
        lifecycle_status=asset.lifecycle_status,
        location=location,
        manufacturer=asset.manufacturer,
        model=asset.model,
        created_at=asset.created_at,
        updated_at=asset.updated_at,
    )


# ---- Plant Service ----

class PlantService:
    def create_plant(self, data: PlantCreate) -> PlantResponse:
        with get_session() as session:
            repo = PlantRepository(session)
            if repo.get_by_id(data.plant_id):
                raise ValueError(f"Plant '{data.plant_id}' already exists")
            plant = Plant(
                plant_id=data.plant_id,
                name=data.name,
                location=data.location,
                timezone=data.timezone,
                status=data.status,
            )
            plant = repo.create(plant)
            return _plant_to_response(plant)

    def get_plant(self, plant_id: str) -> PlantResponse:
        with get_session() as session:
            repo = PlantRepository(session)
            plant = repo.get_by_id(plant_id)
            if not plant:
                raise ValueError(f"Plant '{plant_id}' not found")
            return _plant_to_response(plant)

    def list_plants(self) -> list[PlantResponse]:
        with get_session() as session:
            repo = PlantRepository(session)
            plants = repo.list_all()
            return [_plant_to_response(p) for p in plants]


# ---- Area Service ----

class AreaService:
    def create_area(self, data: AreaCreate) -> AreaResponse:
        with get_session() as session:
            plant_repo = PlantRepository(session)
            plant = plant_repo.get_by_id(data.plant_id)
            if not plant:
                raise ValueError(f"Plant '{data.plant_id}' not found")

            area_repo = AreaRepository(session)
            if area_repo.get_by_id(data.area_id):
                raise ValueError(f"Area '{data.area_id}' already exists")

            area = Area(
                area_id=data.area_id,
                plant_id_fk=plant.id,
                name=data.name,
                area_type=data.area_type,
                status=data.status,
            )
            area = area_repo.create(area)
            return _area_to_response(area)

    def get_area(self, area_id: str) -> AreaResponse:
        with get_session() as session:
            repo = AreaRepository(session)
            area = repo.get_by_id(area_id)
            if not area:
                raise ValueError(f"Area '{area_id}' not found")
            return _area_to_response(area)

    def list_areas(self, plant_id: str | None = None) -> list[AreaResponse]:
        with get_session() as session:
            repo = AreaRepository(session)
            areas = repo.list_by_plant(plant_id)
            return [_area_to_response(a) for a in areas]


# ---- Asset Service ----

class AssetService:
    def create_asset(self, data: AssetCreate) -> AssetResponse:
        with get_session() as session:
            asset_repo = AssetRepository(session)
            if asset_repo.get_by_id(data.asset_id):
                raise ValueError(f"Asset '{data.asset_id}' already exists")

            # Resolve area
            area = None
            if data.area_id:
                area_repo = AreaRepository(session)
                area = area_repo.get_by_id(data.area_id)
                if not area:
                    raise ValueError(f"Area '{data.area_id}' not found")

            # Resolve parent
            parent = None
            if data.parent_asset_id:
                parent = asset_repo.get_by_id(data.parent_asset_id)
                if not parent:
                    raise ValueError(f"Parent asset '{data.parent_asset_id}' not found")

            location_lat = data.location.lat if data.location else None
            location_lng = data.location.lng if data.location else None

            asset = Asset(
                asset_id=data.asset_id,
                asset_code=data.asset_code,
                name=data.name,
                asset_type=data.asset_type,
                area_id_fk=area.id if area else None,
                parent_asset_id_fk=parent.id if parent else None,
                criticality=data.criticality,
                lifecycle_status=data.lifecycle_status,
                location_lat=location_lat,
                location_lng=location_lng,
                manufacturer=data.manufacturer,
                model=data.model,
            )
            asset = asset_repo.create(asset)
            return _asset_to_response(asset)

    def get_asset(self, asset_id: str) -> AssetResponse:
        with get_session() as session:
            repo = AssetRepository(session)
            asset = repo.get_by_id(asset_id)
            if not asset:
                raise ValueError(f"Asset '{asset_id}' not found")
            return _asset_to_response(asset)

    def list_assets(
        self,
        plant_id: str | None = None,
        area_id: str | None = None,
        asset_type: str | None = None,
    ) -> list[AssetResponse]:
        with get_session() as session:
            repo = AssetRepository(session)
            assets = repo.list_all(plant_id=plant_id, area_id=area_id, asset_type=asset_type)
            return [_asset_to_response(a) for a in assets]

    def update_asset(self, asset_id: str, data: AssetUpdate) -> AssetResponse:
        with get_session() as session:
            asset_repo = AssetRepository(session)
            asset = asset_repo.get_by_id(asset_id)
            if not asset:
                raise ValueError(f"Asset '{asset_id}' not found")

            update_data = data.model_dump(exclude_unset=True)

            # Resolve area if changing
            if "area_id" in update_data:
                aid = update_data.pop("area_id")
                if aid:
                    area_repo = AreaRepository(session)
                    area = area_repo.get_by_id(aid)
                    if not area:
                        raise ValueError(f"Area '{aid}' not found")
                    update_data["area_id_fk"] = area.id
                else:
                    update_data["area_id_fk"] = None

            # Resolve parent if changing
            if "parent_asset_id" in update_data:
                pid = update_data.pop("parent_asset_id")
                if pid:
                    parent = asset_repo.get_by_id(pid)
                    if not parent:
                        raise ValueError(f"Parent asset '{pid}' not found")
                    update_data["parent_asset_id_fk"] = parent.id
                else:
                    update_data["parent_asset_id_fk"] = None

            # Flatten location
            if "location" in update_data:
                loc = update_data.pop("location")
                update_data["location_lat"] = loc.lat if loc else None
                update_data["location_lng"] = loc.lng if loc else None

            asset = asset_repo.update(asset, update_data)
            return _asset_to_response(asset)
```

### 6. `backend/app/modules/assets/router.py` — Routes

```python
"""Asset Registry — FastAPI router."""

from fastapi import APIRouter, HTTPException, Query

from app.modules.assets.schemas import (
    PlantCreate,
    PlantResponse,
    AreaCreate,
    AreaResponse,
    AssetCreate,
    AssetUpdate,
    AssetResponse,
)
from app.modules.assets.service import PlantService, AreaService, AssetService

router = APIRouter()

plant_service = PlantService()
area_service = AreaService()
asset_service = AssetService()


# ---- Plants ----

@router.post("/plants", response_model=PlantResponse, status_code=201)
def create_plant(data: PlantCreate):
    try:
        return plant_service.create_plant(data)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.get("/plants", response_model=list[PlantResponse])
def list_plants():
    return plant_service.list_plants()


@router.get("/plants/{plant_id}", response_model=PlantResponse)
def get_plant(plant_id: str):
    try:
        return plant_service.get_plant(plant_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ---- Areas ----

@router.post("/areas", response_model=AreaResponse, status_code=201)
def create_area(data: AreaCreate):
    try:
        return area_service.create_area(data)
    except ValueError as e:
        raise HTTPException(status_code=409 if "already" in str(e) else 404, detail=str(e))


@router.get("/areas", response_model=list[AreaResponse])
def list_areas(plant_id: str | None = Query(None)):
    return area_service.list_areas(plant_id)


@router.get("/areas/{area_id}", response_model=AreaResponse)
def get_area(area_id: str):
    try:
        return area_service.get_area(area_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ---- Assets ----

@router.post("/assets", response_model=AssetResponse, status_code=201)
def create_asset(data: AssetCreate):
    try:
        return asset_service.create_asset(data)
    except ValueError as e:
        raise HTTPException(status_code=409 if "already" in str(e) else 404, detail=str(e))


@router.get("/assets", response_model=list[AssetResponse])
def list_assets(
    plant_id: str | None = Query(None),
    area_id: str | None = Query(None),
    asset_type: str | None = Query(None),
):
    return asset_service.list_assets(plant_id=plant_id, area_id=area_id, asset_type=asset_type)


@router.get("/assets/{asset_id}", response_model=AssetResponse)
def get_asset(asset_id: str):
    try:
        return asset_service.get_asset(asset_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.patch("/assets/{asset_id}", response_model=AssetResponse)
def update_asset(asset_id: str, data: AssetUpdate):
    try:
        return asset_service.update_asset(asset_id, data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
```

### 7. `backend/app/modules/assets/__init__.py` — Module Export

```python
from app.modules.assets.models import Plant, Area, Asset  # noqa: F401
from app.modules.assets.router import router  # noqa: F401
```

### 8. `backend/app/main.py` — Include V1 Router

Thay đổi import và thêm router:

```python
"""PlantOS Center Backend — FastAPI Application."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api import v1_router
from app.core.config import settings
from app.db import get_engine, dispose_engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle."""
    get_engine()
    yield
    dispose_engine()


app = FastAPI(
    title="PlantOS API",
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

app.include_router(v1_router)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
    }
```

### 9. `backend/tests/test_asset_api.py` — API Tests

```python
"""Integration tests for Asset Registry API."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.db.base import Base
from sqlalchemy import create_engine


@pytest.fixture(scope="module")
def test_engine():
    """Create a test database engine."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture(autouse=True)
def setup_db(test_engine, monkeypatch):
    """Override get_session to use test database."""
    from sqlalchemy.orm import sessionmaker
    TestSession = sessionmaker(bind=test_engine, expire_on_commit=False)

    # Override get_session to use test DB
    import app.db.base as db_base
    monkeypatch.setattr(db_base, "_SessionLocal", TestSession)

    # Clear tables before each test
    for table in reversed(Base.metadata.sorted_tables):
        with test_engine.connect() as conn:
            conn.execute(table.delete())
            conn.commit()


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


# ---- Plant Tests ----

@pytest.mark.asyncio
async def test_create_plant(client):
    resp = await client.post("/api/v1/plants", json={
        "plant_id": "DEMO-PLANT",
        "name": "Demo Plant",
        "timezone": "Asia/Ho_Chi_Minh",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["plant_id"] == "DEMO-PLANT"
    assert data["name"] == "Demo Plant"


@pytest.mark.asyncio
async def test_create_plant_duplicate(client):
    await client.post("/api/v1/plants", json={"plant_id": "DUP", "name": "X"})
    resp = await client.post("/api/v1/plants", json={"plant_id": "DUP", "name": "Y"})
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_list_plants(client):
    await client.post("/api/v1/plants", json={"plant_id": "P1", "name": "P1"})
    await client.post("/api/v1/plants", json={"plant_id": "P2", "name": "P2"})
    resp = await client.get("/api/v1/plants")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


@pytest.mark.asyncio
async def test_get_plant_not_found(client):
    resp = await client.get("/api/v1/plants/NONEXISTENT")
    assert resp.status_code == 404


# ---- Area Tests ----

@pytest.mark.asyncio
async def test_create_area(client):
    await client.post("/api/v1/plants", json={"plant_id": "DEMO-PLANT", "name": "X"})
    resp = await client.post("/api/v1/areas", json={
        "area_id": "PROCESS-AREA",
        "plant_id": "DEMO-PLANT",
        "name": "Process Area",
    })
    assert resp.status_code == 201
    assert resp.json()["area_id"] == "PROCESS-AREA"


@pytest.mark.asyncio
async def test_create_area_plant_not_found(client):
    resp = await client.post("/api/v1/areas", json={
        "area_id": "A1", "plant_id": "NOPLANT", "name": "A",
    })
    assert resp.status_code == 404


# ---- Asset Tests ----

@pytest.fixture
async def setup_plant_area(client):
    """Create prerequisite Plant + Area for asset tests."""
    await client.post("/api/v1/plants", json={"plant_id": "DEMO-PLANT", "name": "DP"})
    await client.post("/api/v1/areas", json={
        "area_id": "PROCESS-AREA", "plant_id": "DEMO-PLANT", "name": "PA",
    })


@pytest.mark.asyncio
async def test_create_asset(client, setup_plant_area):
    resp = await client.post("/api/v1/assets", json={
        "asset_id": "PUMP-101",
        "name": "Feed Pump 101",
        "asset_type": "pump",
        "area_id": "PROCESS-AREA",
        "criticality": "medium",
        "location": {"lat": 10.76, "lng": 106.66},
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["asset_id"] == "PUMP-101"
    assert data["asset_type"] == "pump"
    assert data["area_id"] == "PROCESS-AREA"
    assert data["plant_id"] == "DEMO-PLANT"
    assert data["location"]["lat"] == 10.76


@pytest.mark.asyncio
async def test_get_asset(client, setup_plant_area):
    await client.post("/api/v1/assets", json={
        "asset_id": "PUMP-101", "name": "Pump", "asset_type": "pump",
    })
    resp = await client.get("/api/v1/assets/PUMP-101")
    assert resp.status_code == 200
    assert resp.json()["name"] == "Pump"


@pytest.mark.asyncio
async def test_get_asset_not_found(client):
    resp = await client.get("/api/v1/assets/NOEXIST")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_list_assets(client, setup_plant_area):
    await client.post("/api/v1/assets", json={
        "asset_id": "PUMP-101", "name": "Pump", "asset_type": "pump",
    })
    await client.post("/api/v1/assets", json={
        "asset_id": "VALVE-101", "name": "Valve", "asset_type": "valve",
        "area_id": "PROCESS-AREA",
    })
    resp = await client.get("/api/v1/assets")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


@pytest.mark.asyncio
async def test_list_assets_filter_type(client, setup_plant_area):
    await client.post("/api/v1/assets", json={
        "asset_id": "PUMP-101", "name": "Pump", "asset_type": "pump",
    })
    await client.post("/api/v1/assets", json={
        "asset_id": "VALVE-101", "name": "Valve", "asset_type": "valve",
    })
    resp = await client.get("/api/v1/assets?asset_type=pump")
    assert resp.status_code == 200
    assert len(resp.json()) == 1
    assert resp.json()[0]["asset_type"] == "pump"


@pytest.mark.asyncio
async def test_update_asset(client, setup_plant_area):
    await client.post("/api/v1/assets", json={
        "asset_id": "PUMP-101", "name": "Old", "asset_type": "pump",
    })
    resp = await client.patch("/api/v1/assets/PUMP-101", json={
        "name": "New Name",
        "criticality": "high",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "New Name"
    assert data["criticality"] == "high"
    assert data["asset_type"] == "pump"  # unchanged


@pytest.mark.asyncio
async def test_create_asset_duplicate(client, setup_plant_area):
    await client.post("/api/v1/assets", json={
        "asset_id": "PUMP-101", "name": "P1", "asset_type": "pump",
    })
    resp = await client.post("/api/v1/assets", json={
        "asset_id": "PUMP-101", "name": "P2", "asset_type": "pump",
    })
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_health_still_works(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "healthy"
```

## Constraints

- [x] Router chỉ gọi Service — KHÔNG gọi repository trực tiếp
- [x] Service chỉ gọi Repository — KHÔNG gọi SQLAlchemy session trực tiếp
- [x] Không bypass UNS/CDM — Asset API sử dụng asset_id business key, không raw tag
- [x] Không UI-to-DB coupling — tất cả access qua API layer
- [x] Schema API khớp contract `docs/14-api-contract-mvp.md` §4
- [x] Location là nested object trong API → flat lat/lng trong DB model
- [x] plant_id/area_id là business key string trong API → resolved trong service
- [x] Test dùng SQLite in-memory — không cần PostgreSQL

## Validation

1. **Run all tests:**
   ```bash
   cd backend
   python -m pytest tests/ -v
   ```
   Expected: ~25+ tests passed (15 cũ + ~10 mới)

2. **Manual API test:**
   ```bash
   cd backend
   uvicorn app.main:app --port 8000 &
   curl -X POST http://localhost:8000/api/v1/plants -H "Content-Type: application/json" -d '{"plant_id":"DEMO-PLANT","name":"Demo"}'
   curl http://localhost:8000/api/v1/plants
   ```

3. **Health endpoint still works:**
   ```bash
   curl http://localhost:8000/health
   ```

## Expected Output Format

```
1. Files created/modified:
   - [list all 9 files with status]

2. Test results:
   - Total: XX passed
   - test_asset_api.py: XX/XX PASSED
   - All previous tests: 15/15 PASSED (regression)

3. 4-Layer Pattern Verification:
   - Router → Service → Repository → Model ✅
   - Router never calls repository directly ✅
   - Service never uses raw SQLAlchemy session ✅

4. Issues / Deviations:
   - [list]

5. Confirmation:
   - [x] API contract matches docs/14-api-contract-mvp.md §4
   - [x] No constitution rule violated
   - [x] No UI-to-DB coupling
   - [x] 4-layer pattern established for all future modules
```
