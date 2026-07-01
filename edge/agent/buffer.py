"""DuckDB local time-series buffer — per ADR-0003."""

import duckdb
from datetime import datetime, timedelta, timezone


class DuckDBBuffer:
    def __init__(self, path: str = "edge_data.duckdb", retention_days: int = 60):
        self.path = path
        self.retention_days = retention_days
        self.conn = duckdb.connect(path)
        self._init_schema()

    def _init_schema(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS measurements (
                ts          TIMESTAMPTZ NOT NULL,
                signal_id   VARCHAR NOT NULL,
                value       DOUBLE,
                quality     VARCHAR,
                source      VARCHAR,
                synced      BOOLEAN DEFAULT FALSE,
                retry_count INTEGER DEFAULT 0
            )
        """)
        # Migration: add retry_count column if upgrading existing database
        try:
            self.conn.execute("ALTER TABLE measurements ADD COLUMN retry_count INTEGER DEFAULT 0")
        except Exception:
            pass  # Column already exists
        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_meas_signal_ts
            ON measurements(signal_id, ts)
        """)

    def write(self, measurements: list[dict]):
        """Write batch of measurements to local buffer."""
        for m in measurements:
            self.conn.execute("""
                INSERT INTO measurements (ts, signal_id, value, quality, source, synced)
                VALUES (?, ?, ?, ?, ?, FALSE)
            """, [m["timestamp"], m["signal_id"], m["value"], m.get("quality", "GOOD"), m.get("source", "edge")])

    def get_unsynced(self, limit: int = 1000, max_retries: int = 3) -> list[dict]:
        """Get measurements not yet synced to Center, excluding dead letters."""
        rows = self.conn.execute("""
            SELECT ts, signal_id, value, quality, source, retry_count
            FROM measurements WHERE synced = FALSE AND retry_count < ?
            ORDER BY ts ASC LIMIT ?
        """, [max_retries, limit]).fetchall()
        return [
            {"timestamp": r[0].isoformat(), "signal_id": r[1], "value": r[2],
             "quality": r[3], "source": r[4], "retry_count": r[5]}
            for r in rows
        ]

    def mark_synced(self, count: int):
        """Mark oldest N unsynced rows as synced."""
        self.conn.execute("""
            UPDATE measurements SET synced = TRUE
            WHERE rowid IN (
                SELECT rowid FROM measurements WHERE synced = FALSE
                ORDER BY ts ASC LIMIT ?
            )
        """, [count])

    def increment_retry_count(self, count: int):
        """Increment retry_count for oldest N unsynced rows."""
        self.conn.execute("""
            UPDATE measurements SET retry_count = retry_count + 1
            WHERE rowid IN (
                SELECT rowid FROM measurements WHERE synced = FALSE
                ORDER BY ts ASC LIMIT ?
            )
        """, [count])

    def skip_dead_letters(self, max_retries: int = 3) -> int:
        """Mark rows with retry_count >= max_retries as synced (dead letter).
        Returns count of rows skipped.
        """
        # Count before (DuckDB has no changes() function)
        before = self.conn.execute("""
            SELECT COUNT(*) FROM measurements
            WHERE synced = FALSE AND retry_count >= ?
        """, [max_retries]).fetchone()[0]
        if before > 0:
            self.conn.execute("""
                UPDATE measurements SET synced = TRUE
                WHERE synced = FALSE AND retry_count >= ?
            """, [max_retries])
        return before

    def cleanup_retention(self):
        """Delete data older than retention period."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=self.retention_days)
        self.conn.execute("DELETE FROM measurements WHERE ts < ?", [cutoff.isoformat()])

    def count_unsynced(self) -> int:
        return self.conn.execute("SELECT COUNT(*) FROM measurements WHERE synced = FALSE").fetchone()[0]

    def close(self):
        self.conn.close()
