"""TDengine Historian Adapter — the ONLY module that knows TDengine internals."""

import logging
from datetime import datetime, timezone

from app.core.config import settings
from app.db.tdengine import build_tdengine_dsn
from app.modules.historian.interface import HistorianInterface
from app.modules.historian.models import (
    HistorianCapabilities,
    Measurement,
    Quality,
    WriteResult,
)

logger = logging.getLogger(__name__)


class TDengineHistorianAdapter(HistorianInterface):
    """TDengine-backed historian implementation using taos-ws-py (cursor API)."""

    def __init__(self):
        self._conn = None
        self._cursor = None
        self._connected = False
        self._child_tables: set[str] = set()  # Cache known child tables

    async def connect(self) -> bool:
        """Establish WebSocket connection to TDengine and ensure DB/supertable exist.

        In non-dev mode, HISTORIAN_MODE=tdengine will fail if TDengine is unavailable.
        HISTORIAN_MODE=stub is only allowed in development.
        """
        from app.core.config import settings

        mode = settings.HISTORIAN_MODE
        if mode == "stub" and not settings.DEBUG:
            logger.error(
                "HISTORIAN_MODE=stub is only allowed in dev (DEBUG=true). "
                "Set HISTORIAN_MODE=tdengine for non-dev environments."
            )
            return False
        try:
            from taosws import connect

            dsn = build_tdengine_dsn()
            logger.info("Connecting to TDengine at %s", dsn)
            self._conn = connect(dsn)
            self._cursor = self._conn.cursor()

            # Ensure database exists
            self._cursor.execute(
                f"CREATE DATABASE IF NOT EXISTS {settings.TDENGINE_DATABASE} "
                "PRECISION 'ms' DURATION 30"
            )
            self._cursor.execute(f"USE {settings.TDENGINE_DATABASE}")

            # Create supertable for measurements
            # Note: `value` is backtick-escaped because it's a reserved word in TDengine 3.3+
            self._cursor.execute(
                "CREATE STABLE IF NOT EXISTS measurements ("
                "ts TIMESTAMP, "
                "`value` DOUBLE, "
                "quality NCHAR(32), "
                "source NCHAR(128)"
                ") TAGS ("
                "signal_id NCHAR(256), "
                "asset_id NCHAR(128), "
                "signal_name NCHAR(128), "
                "unit NCHAR(64)"
                ")"
            )

            self._connected = True
            logger.info("TDengineHistorianAdapter connected to %s", settings.TDENGINE_HOST)
            return True
        except Exception as e:
            logger.warning("TDengineHistorianAdapter connection failed: %s", e)
            self._connected = False
            return False

    async def _execute(self, sql: str):
        """Execute a SQL statement (DDL/DML) via cursor."""
        if self._cursor is None:
            raise RuntimeError("TDengine not connected")
        try:
            self._cursor.execute(sql)
        except Exception:
            logger.exception("TDengine execute failed: %s", sql[:200])
            raise

    async def _query_dict(self, sql: str) -> list[dict]:
        """Execute a query and return rows as list of dicts via cursor."""
        if self._cursor is None:
            raise RuntimeError("TDengine not connected")
        try:
            self._cursor.execute(sql)
            rows = self._cursor.fetchallintodict()
            return rows if rows else []
        except Exception:
            logger.exception("TDengine query failed: %s", sql[:200])
            raise

    def _safe_name(self, signal_id: str) -> str:
        """Convert signal_id to a safe TDengine child table name."""
        safe = signal_id.replace(".", "_").replace("-", "_").replace(":", "_")
        safe = safe.replace("/", "_").replace(" ", "_")
        safe = safe.lower()
        # Collapse letter_number sequences: comp_01 -> comp01
        import re
        safe = re.sub(r'([a-z])_(\d)', r'\1\2', safe)
        safe = re.sub(r'(\d)_([a-z])', r'\1\2', safe)
        return safe

    async def _ensure_child_table(self, signal_id: str):
        """Ensure a child table exists for the given signal_id."""
        safe_name = self._safe_name(signal_id)
        self._cursor.execute(
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

        # Group by signal_id for batch insert
        groups: dict[str, list[Measurement]] = {}
        for m in measurements:
            groups.setdefault(m.signal_id, []).append(m)

        for signal_id, batch in groups.items():
            try:
                safe_name = self._safe_name(signal_id)

                # Ensure child table exists (cached)
                if safe_name not in self._child_tables:
                    await self._ensure_child_table(signal_id)
                    self._child_tables.add(safe_name)

                # Batch INSERT: multiple VALUES in one SQL
                values = []
                for m in batch:
                    ts_str = m.timestamp.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                    val_str = "NULL" if m.value is None else str(m.value)
                    values.append(
                        f"('{ts_str}', {val_str}, "
                        f"'{m.quality.value}', '{m.source}')"
                    )

                sql = f"INSERT INTO d_{safe_name} VALUES {', '.join(values)}"
                self._cursor.execute(sql)
                accepted += len(batch)
            except Exception as e:
                rejected += len(batch)
                errors.append(f"{signal_id}: {e}")

        return WriteResult(accepted=accepted, rejected=rejected, errors=errors)

    async def query_latest(self, signal_ids: list[str]) -> dict[str, Measurement | None]:
        if not self._connected:
            return {sid: None for sid in signal_ids}

        result = {}
        for sid in signal_ids:
            try:
                safe_name = self._safe_name(sid)
                self._cursor.execute(
                    f"SELECT ts, `value` as val, quality, source FROM d_{safe_name} ORDER BY ts DESC LIMIT 1"
                )
                dict_rows = self._cursor.fetchallintodict()
                if dict_rows:
                    r = dict_rows[0]
                    result[sid] = Measurement(
                        timestamp=r["ts"],
                        signal_id=sid,
                        value=r["val"],
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

        safe_name = self._safe_name(signal_id)
        try:
            from_str = from_ts.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            to_str = to_ts.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

            if interval:
                sql = (
                    f"SELECT ts, `value` as val, quality, source FROM d_{safe_name} "
                    f"WHERE ts >= '{from_str}' AND ts <= '{to_str}' "
                    f"INTERVAL({interval})"
                )
            else:
                sql = (
                    f"SELECT ts, `value` as val, quality, source FROM d_{safe_name} "
                    f"WHERE ts >= '{from_str}' AND ts <= '{to_str}'"
                )
            self._cursor.execute(sql)
            rows = self._cursor.fetchallintodict()
            return [
                Measurement(
                    timestamp=r["ts"].replace(tzinfo=timezone.utc) if isinstance(r["ts"], datetime) else r["ts"],
                    signal_id=signal_id,
                    value=r["val"],
                    quality=Quality(r.get("quality", "GOOD")),
                    source=r.get("source", "unknown"),
                )
                for r in (rows or [])
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
            self._cursor.execute("SELECT 1")
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
        if self._cursor:
            try:
                self._cursor.close()
            except Exception:
                pass
            self._cursor = None
        if self._conn:
            try:
                self._conn.close()
            except Exception:
                pass
            self._conn = None
        self._connected = False
