"""Integration tests for Measurement API."""

import os
import sys
import tempfile
from datetime import datetime, timedelta, timezone

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine

import app.modules as _modules  # noqa: F401

from app.main import app as _app
from app.db.base import Base
from app.modules.historian.stub_adapter import StubHistorianAdapter


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


@pytest.fixture(autouse=True)
def setup_historian():
    """Force get_historian singleton to use Stub adapter per test."""
    router_mod = sys.modules.get("app.modules.measurements.router")
    if router_mod is not None:
        router_mod._historian_instance = StubHistorianAdapter()


@pytest.fixture
async def client():
    transport = ASGITransport(app=_app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.fixture
async def setup_signal(client):
    """Create Plant -> Area -> Asset -> Signal prerequisites."""
    await client.post("/api/v1/plants", json={"plant_id": "DEMO-PLANT", "name": "DP"})
    await client.post(
        "/api/v1/areas",
        json={"area_id": "PROCESS-AREA", "plant_id": "DEMO-PLANT", "name": "PA"},
    )
    await client.post(
        "/api/v1/assets",
        json={"asset_id": "PUMP-101", "name": "Pump", "asset_type": "pump"},
    )
    await client.post(
        "/api/v1/signals",
        json={
            "signal_id": "PUMP-101.discharge_pressure",
            "asset_id": "PUMP-101",
            "signal_name": "discharge_pressure",
            "engineering_unit": "bar",
        },
    )
    await client.post(
        "/api/v1/signals",
        json={
            "signal_id": "PUMP-101.flow_rate",
            "asset_id": "PUMP-101",
            "signal_name": "flow_rate",
            "engineering_unit": "l/min",
        },
    )


# ---- Ingest Tests ----

@pytest.mark.asyncio
async def test_ingest_batch(client, setup_signal):
    """Verify batch ingestion returns accepted count."""
    now = datetime.now(timezone.utc)
    resp = await client.post(
        "/api/v1/measurements/ingest",
        json={
            "source": "test-edge",
            "measurements": [
                {
                    "timestamp": now.isoformat(),
                    "signal_id": "PUMP-101.discharge_pressure",
                    "value": 7.2,
                    "quality": "GOOD",
                },
                {
                    "timestamp": now.isoformat(),
                    "signal_id": "PUMP-101.flow_rate",
                    "value": 100.5,
                    "quality": "GOOD",
                },
            ],
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["accepted"] == 2
    assert data["rejected"] == 0
    assert len(data["errors"]) == 0


@pytest.mark.asyncio
async def test_ingest_unknown_signal(client, setup_signal):
    """Verify unknown signal is rejected without crash."""
    now = datetime.now(timezone.utc)
    resp = await client.post(
        "/api/v1/measurements/ingest",
        json={
            "source": "test",
            "measurements": [
                {
                    "timestamp": now.isoformat(),
                    "signal_id": "UNKNOWN.signal",
                    "value": 42.0,
                    "quality": "GOOD",
                },
                {
                    "timestamp": now.isoformat(),
                    "signal_id": "PUMP-101.discharge_pressure",
                    "value": 7.2,
                    "quality": "GOOD",
                },
            ],
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["accepted"] == 1
    assert data["rejected"] == 1
    assert any("UNKNOWN" in e for e in data["errors"])


# ---- Current Value Tests ----

@pytest.mark.asyncio
async def test_get_current_by_signal(client, setup_signal):
    """Verify current value query by signal_id."""
    now = datetime.now(timezone.utc)
    await client.post(
        "/api/v1/measurements/ingest",
        json={
            "source": "test",
            "measurements": [
                {
                    "timestamp": now.isoformat(),
                    "signal_id": "PUMP-101.discharge_pressure",
                    "value": 7.5,
                    "quality": "GOOD",
                }
            ],
        },
    )
    resp = await client.get(
        "/api/v1/measurements/current?signal_id=PUMP-101.discharge_pressure"
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["signal_id"] == "PUMP-101.discharge_pressure"
    assert data[0]["value"] == 7.5
    assert data[0]["asset_id"] == "PUMP-101"


@pytest.mark.asyncio
async def test_get_current_by_asset(client, setup_signal):
    """Verify current value query by asset_id returns all signals."""
    now = datetime.now(timezone.utc)
    await client.post(
        "/api/v1/measurements/ingest",
        json={
            "source": "test",
            "measurements": [
                {
                    "timestamp": now.isoformat(),
                    "signal_id": "PUMP-101.discharge_pressure",
                    "value": 7.5,
                    "quality": "GOOD",
                },
                {
                    "timestamp": now.isoformat(),
                    "signal_id": "PUMP-101.flow_rate",
                    "value": 50.0,
                    "quality": "GOOD",
                },
            ],
        },
    )
    resp = await client.get("/api/v1/measurements/current?asset_id=PUMP-101")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    ids = {d["signal_id"] for d in data}
    assert "PUMP-101.discharge_pressure" in ids
    assert "PUMP-101.flow_rate" in ids


@pytest.mark.asyncio
async def test_get_current_no_params(client):
    """Verify current query without params returns 400."""
    resp = await client.get("/api/v1/measurements/current")
    assert resp.status_code == 400


# ---- History Tests ----

@pytest.mark.asyncio
async def test_get_history(client, setup_signal):
    """Verify history query returns time-series data."""
    now = datetime.now(timezone.utc)
    await client.post(
        "/api/v1/measurements/ingest",
        json={
            "source": "test",
            "measurements": [
                {
                    "timestamp": now.isoformat(),
                    "signal_id": "PUMP-101.discharge_pressure",
                    "value": 7.2,
                    "quality": "GOOD",
                }
            ],
        },
    )
    from_ts = (now.replace(microsecond=0) - timedelta(seconds=1)).isoformat()
    to_ts = (now.replace(microsecond=0) + timedelta(seconds=1)).isoformat()
    resp = await client.get(
        "/api/v1/measurements/history",
        params={
            "signal_id": "PUMP-101.discharge_pressure",
            "from": from_ts,
            "to": to_ts,
        },
    )
    assert resp.status_code == 200, f"History failed: {resp.json()}"
    data = resp.json()
    assert data["signal_id"] == "PUMP-101.discharge_pressure"
    assert len(data["data"]) == 1
    assert data["data"][0]["value"] == 7.2


@pytest.mark.asyncio
async def test_get_history_invalid_timestamp(client):
    """Verify invalid timestamp returns 400."""
    resp = await client.get(
        "/api/v1/measurements/history",
        params={
            "signal_id": "PUMP-101.pressure",
            "from": "invalid",
            "to": "2026-01-01T00:00:00",
        },
    )
    assert resp.status_code == 400
