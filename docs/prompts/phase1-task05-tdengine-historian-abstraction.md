# Phase 1 — Task 5: TDengine Historian Abstraction

> **Designer:** DeepSeek V4 Pro | **Date:** 2026-06-30
> **Coder:** DeepSeek V4 Flash | **Reviewer:** DeepSeek V4 Pro
> **Status:** READY FOR IMPLEMENTATION

## Context

Tạo Historian Service Interface (theo ADR-0002) và TDengineHistorianAdapter. Đây là abstraction layer duy nhất biết TDengine schema — mọi module khác (API, Rule, UI) chỉ gọi qua interface này.

**Môi trường:** Docker có sẵn trên máy (`Docker 29.5.3`). TDengine sẽ chạy qua Docker Compose (`tdengine/tdengine:3.3.4.0`). Coder cần start TDengine container để test adapter thật.

## Plan Reference

- `docs/adr/ADR-0002-historian-abstraction-performance-reliability.md` — Interface contract, capability model
- `docs/15-storage-and-historian-design.md` §5-8 — Historian responsibilities, measurement schema
- `docs/20-data-model.md` §3 — Measurement canonical object
- `deployment/docker-compose.yml` — TDengine service config

## Implementation Checklist

- [ ] MODIFY `backend/pyproject.toml` — thêm `taos-ws-py>=0.6.0`
- [ ] MODIFY `backend/app/core/config.py` — thêm TDengine connection fields
- [ ] CREATE `backend/app/db/tdengine.py` — TDengine connection manager
- [ ] CREATE `backend/app/modules/historian/models.py` — Measurement Pydantic + Capabilities model
- [ ] CREATE `backend/app/modules/historian/interface.py` — `HistorianInterface` ABC
- [ ] CREATE `backend/app/modules/historian/tdengine_adapter.py` — `TDengineHistorianAdapter`
- [ ] CREATE `backend/app/modules/historian/stub_adapter.py` — `StubHistorianAdapter` (in-memory, cho test không cần TDengine)
- [ ] MODIFY `backend/app/modules/historian/__init__.py` — export interface + adapters
- [ ] CREATE `backend/tests/test_historian_interface.py` — test interface contract với Stub
- [ ] CREATE `backend/tests/test_tdengine_adapter.py` — test adapter thật với Docker TDengine (skip nếu không connect được)
- [ ] VERIFY: start TDengine Docker, run adapter tests

## Exact Files to Create/Modify

| # | File Path | Action | Content Summary |
|---|-----------|--------|-----------------|
| 1 | `backend/pyproject.toml` | MODIFY | Add `taos-ws-py>=0.6.0` to dependencies |
| 2 | `backend/app/core/config.py` | MODIFY | Add TDengine user/password/timeout config |
| 3 | `backend/app/db/tdengine.py` | CREATE | TDengine connection manager (async context) |
| 4 | `backend/app/modules/historian/models.py` | CREATE | `Measurement`, `HistorianCapabilities`, `WriteResult` |
| 5 | `backend/app/modules/historian/interface.py` | CREATE | `HistorianInterface` ABC |
| 6 | `backend/app/modules/historian/tdengine_adapter.py` | CREATE | `TDengineHistorianAdapter` implementation |
| 7 | `backend/app/modules/historian/stub_adapter.py` | CREATE | `StubHistorianAdapter` in-memory implementation |
| 8 | `backend/app/modules/historian/__init__.py` | MODIFY | Export interface + both adapters |
| 9 | `backend/tests/test_historian_interface.py` | CREATE | Interface contract tests (uses Stub) |
| 10 | `backend/tests/test_tdengine_adapter.py` | CREATE | Integration test with real TDengine (skip if unavailable) |

## Detailed Instructions

### 1. `backend/pyproject.toml` — Add TDengine Dependency

Thêm `"taos-ws-py>=0.6.0"` vào `dependencies` list, sau dòng `psycopg2-binary`.

### 2. `backend/app/core/config.py` — Add TDengine Connection Settings

Thêm vào class `Settings`:

```python
# TDengine (expanded)
TDENGINE_USER: str = "root"
TDENGINE_PASSWORD: str = "taosdata"
TDENGINE_TIMEOUT: int = 10  # connection timeout in seconds
```

### 3. `backend/app/db/tdengine.py` — TDengine Connection Manager

```python
"""TDengine connection manager using taos-ws-py (WebSocket)."""

import logging
from contextlib import asynccontextmanager

from taosws import connect

from app.core.config import settings

logger = logging.getLogger(__name__)


def build_tdengine_dsn() -> str:
    """Build TDengine WebSocket DSN from settings."""
    return (
        f"taosws://{settings.TDENGINE_USER}:{settings.TDENGINE_PASSWORD}"
        f"@{settings.TDENGINE_HOST}:{settings.TDENGINE_PORT}"
    )


async def get_tdengine_connection():
    """Create an async TDengine WebSocket connection."""
    dsn = build_tdengine_dsn()
    conn = connect(dsn)
    return conn


async def ensure_database(conn):
    """Ensure the PlantOS database exists in TDengine."""
    await conn.execute(f"CREATE DATABASE IF NOT EXISTS {settings.TDENGINE_DATABASE}")
    await conn.execute(f"USE {settings.TDENGINE_DATABASE}")
```

> Lưu ý: `taosws.connect()` có thể là sync. Nếu vậy, dùng `asyncio.to_thread()` hoặc gọi sync trong `__init__` của adapter. Kiểm tra API của `taos-ws-py==0.6.9` — nếu chỉ có sync API, adapter sẽ dùng sync trong `async def` với `run_in_executor`.

### 4. `backend/app/modules/historian/models.py` — Measurement & Capabilities

```python
"""Historian domain models — canonical Measurement object."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class Quality(str, Enum):
    """Measurement quality values per OPC UA / PlantOS convention."""
    GOOD = "GOOD"
    BAD = "BAD"
    UNCERTAIN = "UNCERTAIN"
    STALE = "STALE"
    SIMULATED = "SIMULATED"
    MANUAL = "MANUAL"
    ESTIMATED = "ESTIMATED"
    MISSING = "MISSING"


class Measurement(BaseModel):
    """Canonical measurement object — matches docs/20-data-model.md §3."""
    timestamp: datetime
    signal_id: str
    value: float | bool | None = None
    quality: Quality = Quality.GOOD
    source: str = "unknown"


class HistorianCapabilities(BaseModel):
    """Capabilities exposed by a historian backend — per ADR-0002."""
    backend: str
    supports_write: bool = True
    supports_batch_write: bool = True
    supports_latest_query: bool = True
    supports_aggregation: bool = False
    supports_downsampling: bool = False
    supports_backfill: bool = False
    supports_string_values: bool = False
    supports_quality: bool = True
    supports_external_tag_mapping: bool = False


class WriteResult(BaseModel):
    """Result of a batch write operation."""
    accepted: int = 0
    rejected: int = 0
    errors: list[str] = Field(default_factory=list)
```

### 5. `backend/app/modules/historian/interface.py` — HistorianInterface ABC

```python
"""Historian Service Interface — per ADR-0002."""

from abc import ABC, abstractmethod
from datetime import datetime

from app.modules.historian.models import (
    HistorianCapabilities,
    Measurement,
    WriteResult,
)


class HistorianInterface(ABC):
    """Abstract interface for PlantOS historian backends.

    Only TDengineHistorianAdapter implementation may know TDengine-specific
    schema, SQL, driver, or connection methods.
    """

    @abstractmethod
    async def write_measurements(self, measurements: list[Measurement]) -> WriteResult:
        """Write a batch of measurements. Must be idempotent where possible."""
        ...

    @abstractmethod
    async def query_latest(self, signal_ids: list[str]) -> dict[str, Measurement | None]:
        """Get latest measurement for each signal_id."""
        ...

    @abstractmethod
    async def query_history(
        self,
        signal_id: str,
        from_ts: datetime,
        to_ts: datetime,
        interval: str | None = None,
    ) -> list[Measurement]:
        """Query historical measurements for a single signal."""
        ...

    @abstractmethod
    async def query_multi_history(
        self,
        signal_ids: list[str],
        from_ts: datetime,
        to_ts: datetime,
        interval: str | None = None,
    ) -> dict[str, list[Measurement]]:
        """Query historical measurements for multiple signals."""
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the historian backend is reachable and healthy."""
        ...

    @abstractmethod
    def get_capabilities(self) -> HistorianCapabilities:
        """Return backend capabilities — per ADR-0002 capability model."""
        ...
```

### 6. `backend/app/modules/historian/tdengine_adapter.py` — TDengineHistorianAdapter

```python
"""TDengine Historian Adapter — the ONLY module that knows TDengine internals."""

import logging
from datetime import datetime

from app.core.config import settings
from app.db.tdengine import build_tdengine_dsn, ensure_database
from app.modules.historian.interface import HistorianInterface
from app.modules.historian.models import (
    HistorianCapabilities,
    Measurement,
    Quality,
    WriteResult,
)

logger = logging.getLogger(__name__)


class TDengineHistorianAdapter(HistorianInterface):
    """TDengine-backed historian implementation using taos-ws-py."""

    def __init__(self):
        self._conn = None
        self._connected = False

    async def connect(self) -> bool:
        """Establish WebSocket connection to TDengine and ensure DB/supertable exist."""
        try:
            from taosws import connect  # WebSocket connector

            dsn = build_tdengine_dsn()
            self._conn = connect(dsn)

            # Ensure database exists
            await self._execute(
                f"CREATE DATABASE IF NOT EXISTS {settings.TDENGINE_DATABASE} "
                "PRECISION 'ms' DURATION 30"
            )
            await self._execute(f"USE {settings.TDENGINE_DATABASE}")

            # Create supertable for measurements
            await self._execute("""
                CREATE STABLE IF NOT EXISTS measurements (
                    ts TIMESTAMP,
                    value DOUBLE,
                    quality NCHAR(32),
                    source NCHAR(128)
                ) TAGS (
                    signal_id NCHAR(256),
                    asset_id NCHAR(128),
                    signal_name NCHAR(128),
                    unit NCHAR(64)
                )
            """)

            self._connected = True
            logger.info("TDengineHistorianAdapter connected to %s", settings.TDENGINE_HOST)
            return True
        except Exception as e:
            logger.warning("TDengineHistorianAdapter connection failed: %s", e)
            self._connected = False
            return False

    async def _execute(self, sql: str):
        """Execute a SQL statement. Uses run_in_executor if taosws is sync."""
        # taos-ws-py may be sync — handle both cases
        if self._conn is None:
            raise RuntimeError("TDengine not connected")
        try:
            result = self._conn.execute(sql)
            return result
        except Exception:
            logger.exception("TDengine execute failed: %s", sql[:200])
            raise

    async def _query(self, sql: str) -> list[dict]:
        """Execute a query and return rows as dicts."""
        if self._conn is None:
            raise RuntimeError("TDengine not connected")
        try:
            result = self._conn.query(sql)
            if result is None:
                return []
            # Convert TDengine result to list of dicts
            rows = []
            for row in result:
                rows.append({
                    "ts": row[0],
                    "value": row[1],
                    "quality": row[2],
                    "source": row[3],
                    "signal_id": row[4],
                })
            return rows
        except Exception:
            logger.exception("TDengine query failed: %s", sql[:200])
            raise

    async def _ensure_child_table(self, signal_id: str):
        """Ensure a child table exists for the given signal_id."""
        safe_name = signal_id.replace(".", "_").replace("-", "_")
        await self._execute(
            f"CREATE TABLE IF NOT EXISTS d_{safe_name} "
            f"USING measurements TAGS ('{signal_id}', '', '', '')"
        )

    # ---- Interface Implementation ----

    async def write_measurements(self, measurements: list[Measurement]) -> WriteResult:
        if not self._connected:
            return WriteResult(rejected=len(measurements), errors=["TDengine not connected"])

        accepted = 0
        rejected = 0
        errors = []

        for m in measurements:
            try:
                safe_name = m.signal_id.replace(".", "_").replace("-", "_")
                await self._ensure_child_table(m.signal_id)
                sql = (
                    f"INSERT INTO d_{safe_name} VALUES "
                    f"('{m.timestamp.isoformat()}', {m.value}, "
                    f"'{m.quality.value}', '{m.source}')"
                )
                await self._execute(sql)
                accepted += 1
            except Exception as e:
                rejected += 1
                errors.append(str(e))

        return WriteResult(accepted=accepted, rejected=rejected, errors=errors)

    async def query_latest(self, signal_ids: list[str]) -> dict[str, Measurement | None]:
        if not self._connected:
            return {sid: None for sid in signal_ids}

        result = {}
        for sid in signal_ids:
            try:
                safe_name = sid.replace(".", "_").replace("-", "_")
                rows = await self._query(
                    f"SELECT * FROM d_{safe_name} ORDER BY ts DESC LIMIT 1"
                )
                if rows:
                    r = rows[0]
                    result[sid] = Measurement(
                        timestamp=r["ts"],
                        signal_id=r.get("signal_id", sid),
                        value=r["value"],
                        quality=Quality(r.get("quality", "GOOD")),
                        source=r.get("source", "unknown"),
                    )
                else:
                    result[sid] = None
            except Exception:
                logger.exception("query_latest failed for %s", sid)
                result[sid] = None

        return result

    async def query_history(
        self,
        signal_id: str,
        from_ts: datetime,
        to_ts: datetime,
        interval: str | None = None,
    ) -> list[Measurement]:
        if not self._connected:
            return []

        safe_name = signal_id.replace(".", "_").replace("-", "_")
        try:
            if interval:
                sql = (
                    f"SELECT * FROM d_{safe_name} "
                    f"WHERE ts >= '{from_ts.isoformat()}' AND ts <= '{to_ts.isoformat()}' "
                    f"INTERVAL({interval})"
                )
            else:
                sql = (
                    f"SELECT * FROM d_{safe_name} "
                    f"WHERE ts >= '{from_ts.isoformat()}' AND ts <= '{to_ts.isoformat()}'"
                )
            rows = await self._query(sql)
            return [
                Measurement(
                    timestamp=r["ts"],
                    signal_id=r.get("signal_id", signal_id),
                    value=r["value"],
                    quality=Quality(r.get("quality", "GOOD")),
                    source=r.get("source", "unknown"),
                )
                for r in rows
            ]
        except Exception:
            logger.exception("query_history failed for %s", signal_id)
            return []

    async def query_multi_history(
        self,
        signal_ids: list[str],
        from_ts: datetime,
        to_ts: datetime,
        interval: str | None = None,
    ) -> dict[str, list[Measurement]]:
        if not self._connected:
            return {sid: [] for sid in signal_ids}

        result = {}
        for sid in signal_ids:
            result[sid] = await self.query_history(sid, from_ts, to_ts, interval)
        return result

    async def health_check(self) -> bool:
        if not self._connected:
            return False
        try:
            await self._execute("SELECT 1")
            return True
        except Exception:
            return False

    def get_capabilities(self) -> HistorianCapabilities:
        return HistorianCapabilities(
            backend="tdengine",
            supports_write=True,
            supports_batch_write=True,
            supports_latest_query=True,
            supports_aggregation=True,
            supports_downsampling=False,
            supports_backfill=False,
            supports_string_values=False,
            supports_quality=True,
            supports_external_tag_mapping=False,
        )

    async def close(self):
        """Close the TDengine connection."""
        if self._conn:
            try:
                self._conn.close()
            except Exception:
                pass
            self._connected = False
```

> **Quan trọng:** Coder cần kiểm tra API thực tế của `taos-ws-py==0.6.9`. Các method có thể khác với code mẫu trên. Điều chỉnh phù hợp với thực tế API nhưng phải giữ đúng interface contract. Nếu `taosws` không hỗ trợ async, dùng `asyncio.to_thread()` hoặc `loop.run_in_executor()`.

### 7. `backend/app/modules/historian/stub_adapter.py` — StubHistorianAdapter

```python
"""In-memory stub historian adapter for testing without TDengine."""

from datetime import datetime

from app.modules.historian.interface import HistorianInterface
from app.modules.historian.models import (
    HistorianCapabilities,
    Measurement,
    WriteResult,
)


class StubHistorianAdapter(HistorianInterface):
    """In-memory historian adapter for unit tests.

    Stores measurements in a dict. Does NOT persist to disk.
    """

    def __init__(self):
        self._data: dict[str, list[Measurement]] = {}

    async def write_measurements(self, measurements: list[Measurement]) -> WriteResult:
        accepted = 0
        for m in measurements:
            if m.signal_id not in self._data:
                self._data[m.signal_id] = []
            self._data[m.signal_id].append(m)
            accepted += 1
        return WriteResult(accepted=accepted, rejected=0)

    async def query_latest(self, signal_ids: list[str]) -> dict[str, Measurement | None]:
        result = {}
        for sid in signal_ids:
            rows = self._data.get(sid, [])
            result[sid] = rows[-1] if rows else None
        return result

    async def query_history(
        self,
        signal_id: str,
        from_ts: datetime,
        to_ts: datetime,
        interval: str | None = None,
    ) -> list[Measurement]:
        rows = self._data.get(signal_id, [])
        return [
            m for m in rows
            if from_ts <= m.timestamp <= to_ts
        ]

    async def query_multi_history(
        self,
        signal_ids: list[str],
        from_ts: datetime,
        to_ts: datetime,
        interval: str | None = None,
    ) -> dict[str, list[Measurement]]:
        return {
            sid: await self.query_history(sid, from_ts, to_ts, interval)
            for sid in signal_ids
        }

    async def health_check(self) -> bool:
        return True

    def get_capabilities(self) -> HistorianCapabilities:
        return HistorianCapabilities(
            backend="stub",
            supports_write=True,
            supports_batch_write=True,
            supports_latest_query=True,
            supports_aggregation=False,
            supports_downsampling=False,
            supports_backfill=False,
            supports_string_values=True,
            supports_quality=True,
            supports_external_tag_mapping=False,
        )
```

### 8. `backend/app/modules/historian/__init__.py` — Module Exports

```python
from app.modules.historian.interface import HistorianInterface
from app.modules.historian.models import (
    HistorianCapabilities,
    Measurement,
    Quality,
    WriteResult,
)
from app.modules.historian.stub_adapter import StubHistorianAdapter

__all__ = [
    "HistorianInterface",
    "Measurement",
    "Quality",
    "WriteResult",
    "HistorianCapabilities",
    "StubHistorianAdapter",
]
```

> `TDengineHistorianAdapter` không export ở `__init__.py` để tránh import `taosws` khi không cần. Import trực tiếp từ `app.modules.historian.tdengine_adapter`.

### 9. `backend/tests/test_historian_interface.py` — Interface Contract Tests

```python
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
```

### 10. `backend/tests/test_tdengine_adapter.py` — Real TDengine Integration Test

```python
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
```

## How to Start TDengine for Testing

```bash
# Start TDengine only
docker compose -f deployment/docker-compose.yml up -d tdengine

# Wait for healthy
docker ps --filter name=plantos-tdengine

# Verify
docker exec plantos-tdengine taos -s "show databases"
```

## Constraints

- [x] Chỉ `TDengineHistorianAdapter` mới biết TDengine schema/connector/SQL
- [x] Interface là boundary — mọi module khác gọi qua `HistorianInterface`
- [x] Không UI-to-DB coupling — measurement data chỉ qua interface
- [x] Không hardcode signal_id trong adapter (test dùng ID giả định)
- [x] Edge/Center tách biệt — adapter này cho Center TDengine
- [x] Capability model phải được implement (theo ADR-0002)
- [x] Stub adapter cho phép test không cần TDengine
- [x] Adapter phải xử lý graceful degradation khi TDengine unavailable

## Validation

1. **Interface contract tests (không cần TDengine):**
   ```bash
   cd backend
   python -m pytest tests/test_historian_interface.py -v
   ```
   Expected: 7 tests passed

2. **All existing tests still pass:**
   ```bash
   cd backend
   python -m pytest tests/ -v --ignore=tests/test_tdengine_adapter.py
   ```
   Expected: 12 tests passed (5 models + 7 historian interface)

3. **Start TDengine and run integration tests:**
   ```bash
   docker compose -f deployment/docker-compose.yml up -d tdengine
   # Wait ~20 seconds for TDengine to be healthy
   cd backend
   python -m pytest tests/test_tdengine_adapter.py -v
   ```
   Expected: 3 tests passed (skip nếu TDengine không chạy)

4. **Import check:**
   ```bash
   cd backend
   python -c "from app.modules.historian import HistorianInterface, StubHistorianAdapter; print('OK')"
   ```

## Expected Output Format

```
1. Files created/modified:
   - [list all 10 files with status]

2. Test results:
   - test_historian_interface.py: 7/7 PASSED
   - test_tdengine_adapter.py: 3/3 PASSED (or SKIPPED if no Docker)
   - test_models.py + test_health.py: 5/5 PASSED (regression)

3. TDengine verification:
   - Docker container: running / not running
   - Adapter connect: success / failed
   - Roundtrip test: passed / skipped

4. Issues / Deviations:
   - [API differences between taos-ws-py version and code sample]
   - [Any adjustments made]

5. Confirmation:
   - [x] Only TDengineHistorianAdapter knows TDengine internals
   - [x] No constitution rule violated
   - [x] No UI-to-DB coupling
   - [x] Interface matches ADR-0002 specification
   - [x] Capability model implemented
```
