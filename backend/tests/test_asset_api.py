"""Integration tests for Asset Registry API."""

import os
import tempfile

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine

# Import models first so Base.metadata is populated
import app.modules as _modules  # noqa: F401

from app.main import app as _app
from app.db.base import Base


@pytest.fixture
def test_db_path():
    """Return a temp file path for SQLite."""
    f = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    f.close()
    yield f.name
    os.unlink(f.name)


@pytest.fixture
def test_engine(test_db_path):
    """Create a test database engine using a temp file."""
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
    """Override get_session to use test database."""
    from sqlalchemy.orm import sessionmaker

    TestSession = sessionmaker(bind=test_engine, expire_on_commit=False)

    import app.db.base as db_base

    monkeypatch.setattr(db_base, "_SessionLocal", TestSession)

    # Clear tables before each test
    for table in reversed(Base.metadata.sorted_tables):
        with test_engine.connect() as conn:
            conn.execute(table.delete())
            conn.commit()


@pytest.fixture
async def client():
    transport = ASGITransport(app=_app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


# ---- Plant Tests ----

@pytest.mark.asyncio
async def test_create_plant(client):
    resp = await client.post(
        "/api/v1/plants",
        json={
            "plant_id": "DEMO-PLANT",
            "name": "Demo Plant",
            "timezone": "Asia/Ho_Chi_Minh",
        },
    )
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
    resp = await client.post(
        "/api/v1/areas",
        json={
            "area_id": "PROCESS-AREA",
            "plant_id": "DEMO-PLANT",
            "name": "Process Area",
        },
    )
    assert resp.status_code == 201
    assert resp.json()["area_id"] == "PROCESS-AREA"


@pytest.mark.asyncio
async def test_create_area_plant_not_found(client):
    resp = await client.post(
        "/api/v1/areas",
        json={
            "area_id": "A1",
            "plant_id": "NOPLANT",
            "name": "A",
        },
    )
    assert resp.status_code == 404


# ---- Asset Tests ----


@pytest.fixture
async def setup_plant_area(client):
    """Create prerequisite Plant + Area for asset tests."""
    await client.post("/api/v1/plants", json={"plant_id": "DEMO-PLANT", "name": "DP"})
    await client.post(
        "/api/v1/areas",
        json={
            "area_id": "PROCESS-AREA",
            "plant_id": "DEMO-PLANT",
            "name": "PA",
        },
    )


@pytest.mark.asyncio
async def test_create_asset(client, setup_plant_area):
    resp = await client.post(
        "/api/v1/assets",
        json={
            "asset_id": "PUMP-101",
            "name": "Feed Pump 101",
            "asset_type": "pump",
            "area_id": "PROCESS-AREA",
            "criticality": "medium",
            "location": {"lat": 10.76, "lng": 106.66},
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["asset_id"] == "PUMP-101"
    assert data["asset_type"] == "pump"
    assert data["area_id"] == "PROCESS-AREA"
    assert data["plant_id"] == "DEMO-PLANT"
    assert data["location"]["lat"] == 10.76


@pytest.mark.asyncio
async def test_get_asset(client, setup_plant_area):
    await client.post(
        "/api/v1/assets",
        json={"asset_id": "PUMP-101", "name": "Pump", "asset_type": "pump"},
    )
    resp = await client.get("/api/v1/assets/PUMP-101")
    assert resp.status_code == 200
    assert resp.json()["name"] == "Pump"


@pytest.mark.asyncio
async def test_get_asset_not_found(client):
    resp = await client.get("/api/v1/assets/NOEXIST")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_list_assets(client, setup_plant_area):
    await client.post(
        "/api/v1/assets",
        json={"asset_id": "PUMP-101", "name": "Pump", "asset_type": "pump"},
    )
    await client.post(
        "/api/v1/assets",
        json={
            "asset_id": "VALVE-101",
            "name": "Valve",
            "asset_type": "valve",
            "area_id": "PROCESS-AREA",
        },
    )
    resp = await client.get("/api/v1/assets")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


@pytest.mark.asyncio
async def test_list_assets_filter_type(client, setup_plant_area):
    await client.post(
        "/api/v1/assets",
        json={"asset_id": "PUMP-101", "name": "Pump", "asset_type": "pump"},
    )
    await client.post(
        "/api/v1/assets",
        json={"asset_id": "VALVE-101", "name": "Valve", "asset_type": "valve"},
    )
    resp = await client.get("/api/v1/assets?asset_type=pump")
    assert resp.status_code == 200
    assert len(resp.json()) == 1
    assert resp.json()[0]["asset_type"] == "pump"


@pytest.mark.asyncio
async def test_update_asset(client, setup_plant_area):
    await client.post(
        "/api/v1/assets",
        json={"asset_id": "PUMP-101", "name": "Old", "asset_type": "pump"},
    )
    resp = await client.patch(
        "/api/v1/assets/PUMP-101",
        json={"name": "New Name", "criticality": "high"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "New Name"
    assert data["criticality"] == "high"
    assert data["asset_type"] == "pump"  # unchanged


@pytest.mark.asyncio
async def test_create_asset_duplicate(client, setup_plant_area):
    await client.post(
        "/api/v1/assets",
        json={"asset_id": "PUMP-101", "name": "P1", "asset_type": "pump"},
    )
    resp = await client.post(
        "/api/v1/assets",
        json={"asset_id": "PUMP-101", "name": "P2", "asset_type": "pump"},
    )
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_health_still_works(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "healthy"
