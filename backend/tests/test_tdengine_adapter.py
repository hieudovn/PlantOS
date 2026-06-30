"""Integration tests for TDengineHistorianAdapter.

Requires TDengine running via Docker:
    docker compose -f deployment/docker-compose.yml up -d tdengine

Skip tests if TDengine is not reachable.
"""

import os
from datetime import datetime, timezone

import pytest

from app.modules.historian.models import Measurement, Quality


# Skip all tests if TDengine is not available
def _tdengine_available():
    """Check if TDengine is reachable."""
    try:
        from app.modules.historian.tdengine_adapter import TDengineHistorianAdapter
        import asyncio

        async def check():
            adapter = TDengineHistorianAdapter()
            ok = await adapter.connect()
            await adapter.close()
            return ok

        return asyncio.run(check())
    except Exception:
        return False


pytestmark = pytest.mark.skipif(
    not _tdengine_available(),
    reason="TDengine not available — start with: docker compose up -d tdengine",
)


@pytest.fixture
async def tdengine():
    """Create a connected TDengine adapter."""
    from app.modules.historian.tdengine_adapter import TDengineHistorianAdapter

    adapter = TDengineHistorianAdapter()
    await adapter.connect()
    yield adapter
    await adapter.close()


@pytest.mark.asyncio
async def test_health_check(tdengine):
    """Verify TDengine adapter is healthy."""
    healthy = await tdengine.health_check()
    assert healthy is True


@pytest.mark.asyncio
async def test_write_and_query(tdengine):
    """Verify write + query latest roundtrip."""
    now = datetime.now(timezone.utc)
    m = Measurement(
        timestamp=now,
        signal_id="TEST-PUMP.discharge_pressure",
        value=7.5,
        quality=Quality.SIMULATED,
        source="pytest",
    )

    result = await tdengine.write_measurements([m])
    assert result.accepted == 1
    assert result.rejected == 0

    latest = await tdengine.query_latest(["TEST-PUMP.discharge_pressure"])
    assert latest["TEST-PUMP.discharge_pressure"] is not None
    assert latest["TEST-PUMP.discharge_pressure"].value == 7.5


@pytest.mark.asyncio
async def test_capabilities(tdengine):
    """Verify TDengine capabilities."""
    caps = tdengine.get_capabilities()
    assert caps.backend == "tdengine"
    assert caps.supports_batch_write is True
    assert caps.supports_quality is True
