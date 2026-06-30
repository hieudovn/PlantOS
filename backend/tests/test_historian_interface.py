"""Test HistorianInterface contract using StubHistorianAdapter."""

from datetime import datetime, timezone

import pytest

from app.modules.historian.models import Measurement, Quality
from app.modules.historian.stub_adapter import StubHistorianAdapter


@pytest.fixture
def adapter():
    return StubHistorianAdapter()


@pytest.fixture
def sample_measurements():
    now = datetime.now(timezone.utc)
    return [
        Measurement(
            timestamp=now,
            signal_id="PUMP-101.discharge_pressure",
            value=7.2,
            quality=Quality.SIMULATED,
            source="test",
        ),
        Measurement(
            timestamp=now,
            signal_id="PUMP-101.flow_rate",
            value=100.5,
            quality=Quality.SIMULATED,
            source="test",
        ),
    ]


@pytest.mark.asyncio
async def test_write_measurements(adapter, sample_measurements):
    """Verify batch write returns correct accepted count."""
    result = await adapter.write_measurements(sample_measurements)
    assert result.accepted == 2
    assert result.rejected == 0
    assert len(result.errors) == 0


@pytest.mark.asyncio
async def test_query_latest(adapter, sample_measurements):
    """Verify latest query returns most recent value."""
    await adapter.write_measurements(sample_measurements)

    result = await adapter.query_latest(["PUMP-101.discharge_pressure"])
    assert result["PUMP-101.discharge_pressure"] is not None
    assert result["PUMP-101.discharge_pressure"].value == 7.2

    # Unknown signal returns None
    assert result.get("NONEXISTENT") is None


@pytest.mark.asyncio
async def test_query_history(adapter, sample_measurements):
    """Verify history query with time range."""
    await adapter.write_measurements(sample_measurements)
    ts = sample_measurements[0].timestamp

    result = await adapter.query_history(
        "PUMP-101.discharge_pressure",
        from_ts=ts.replace(second=ts.second - 1),
        to_ts=ts.replace(second=ts.second + 1),
    )
    assert len(result) == 1
    assert result[0].value == 7.2


@pytest.mark.asyncio
async def test_health_check(adapter):
    """Verify stub adapter always reports healthy."""
    assert await adapter.health_check() is True


def test_get_capabilities(adapter):
    """Verify capabilities model is returned."""
    caps = adapter.get_capabilities()
    assert caps.backend == "stub"
    assert caps.supports_write is True
    assert caps.supports_quality is True


def test_measurement_model():
    """Verify Measurement Pydantic model validation."""
    m = Measurement(
        timestamp=datetime.now(timezone.utc),
        signal_id="TEST.signal",
        value=42.0,
        quality=Quality.GOOD,
        source="test",
    )
    assert m.value == 42.0
    assert m.quality == Quality.GOOD


def test_write_result_model():
    """Verify WriteResult model."""
    from app.modules.historian.models import WriteResult
    r = WriteResult(accepted=5, rejected=2, errors=["bad signal"])
    assert r.accepted == 5
    assert len(r.errors) == 1
