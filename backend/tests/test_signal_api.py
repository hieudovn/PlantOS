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
    await client.post(
        "/api/v1/areas",
        json={"area_id": "PROCESS-AREA", "plant_id": "DEMO-PLANT", "name": "PA"},
    )
    await client.post(
        "/api/v1/assets",
        json={"asset_id": "PUMP-101", "name": "Pump", "asset_type": "pump"},
    )


# ---- Signal Tests ----

@pytest.mark.asyncio
async def test_create_signal(client, setup_asset):
    resp = await client.post(
        "/api/v1/signals",
        json={
            "signal_id": "PUMP-101.discharge_pressure",
            "asset_id": "PUMP-101",
            "signal_name": "discharge_pressure",
            "display_name": "Discharge Pressure",
            "engineering_unit": "bar",
            "source": {
                "source_type": "simulator",
                "source_ref": "sim://pump-101/pressure",
            },
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["signal_id"] == "PUMP-101.discharge_pressure"
    assert data["asset_id"] == "PUMP-101"
    assert data["engineering_unit"] == "bar"
    assert data["source"]["source_type"] == "simulator"


@pytest.mark.asyncio
async def test_create_signal_asset_not_found(client):
    resp = await client.post(
        "/api/v1/signals",
        json={
            "signal_id": "X.signal",
            "asset_id": "NOEXIST",
            "signal_name": "x",
        },
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_create_signal_duplicate(client, setup_asset):
    await client.post(
        "/api/v1/signals",
        json={
            "signal_id": "PUMP-101.pressure",
            "asset_id": "PUMP-101",
            "signal_name": "p",
        },
    )
    resp = await client.post(
        "/api/v1/signals",
        json={
            "signal_id": "PUMP-101.pressure",
            "asset_id": "PUMP-101",
            "signal_name": "p2",
        },
    )
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_get_signal(client, setup_asset):
    await client.post(
        "/api/v1/signals",
        json={
            "signal_id": "PUMP-101.pressure",
            "asset_id": "PUMP-101",
            "signal_name": "p",
        },
    )
    resp = await client.get("/api/v1/signals/PUMP-101.pressure")
    assert resp.status_code == 200
    assert resp.json()["signal_name"] == "p"


@pytest.mark.asyncio
async def test_get_signal_not_found(client):
    resp = await client.get("/api/v1/signals/NOEXIST.signal")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_list_signals(client, setup_asset):
    await client.post(
        "/api/v1/signals",
        json={
            "signal_id": "PUMP-101.pressure",
            "asset_id": "PUMP-101",
            "signal_name": "p",
        },
    )
    await client.post(
        "/api/v1/signals",
        json={
            "signal_id": "PUMP-101.flow",
            "asset_id": "PUMP-101",
            "signal_name": "f",
        },
    )
    resp = await client.get("/api/v1/signals")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


@pytest.mark.asyncio
async def test_list_signals_filter_asset(client, setup_asset):
    # Create second asset + signal
    await client.post(
        "/api/v1/assets",
        json={"asset_id": "MOTOR-101", "name": "Motor", "asset_type": "motor"},
    )
    await client.post(
        "/api/v1/signals",
        json={
            "signal_id": "PUMP-101.pressure",
            "asset_id": "PUMP-101",
            "signal_name": "p",
        },
    )
    await client.post(
        "/api/v1/signals",
        json={
            "signal_id": "MOTOR-101.current",
            "asset_id": "MOTOR-101",
            "signal_name": "c",
        },
    )

    resp = await client.get("/api/v1/signals?asset_id=PUMP-101")
    assert resp.status_code == 200
    assert len(resp.json()) == 1
    assert resp.json()[0]["signal_id"] == "PUMP-101.pressure"


@pytest.mark.asyncio
async def test_update_signal(client, setup_asset):
    await client.post(
        "/api/v1/signals",
        json={
            "signal_id": "PUMP-101.pressure",
            "asset_id": "PUMP-101",
            "signal_name": "p",
        },
    )
    resp = await client.patch(
        "/api/v1/signals/PUMP-101.pressure",
        json={
            "display_name": "Updated Pressure",
            "engineering_unit": "kPa",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["display_name"] == "Updated Pressure"
    assert data["engineering_unit"] == "kPa"
    assert data["signal_name"] == "p"  # unchanged
