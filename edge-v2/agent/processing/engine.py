"""ProcessingEngine — applies processing pipeline to raw values.

Manages DuckDB raw_measurements + processed_measurements tables.
Pipeline: raw_value → [step1, step2, ...] → ProcessedReading.
History per signal_id maintained in-memory for moving average.
"""

import logging
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any

from agent.processing.profiles import (
    ProcessingProfile, ProcessingStep, ProcessedReading, MVP_STEP_TYPES,
)
from agent.processing.steps import STEP_REGISTRY

logger = logging.getLogger(__name__)

# Max history length per signal for moving average
MAX_HISTORY = 100


class ProcessingEngine:
    """Applies processing pipeline to raw values.

    - Maintains signal history in-memory for moving average steps
    - Writes raw values to DuckDB raw_measurements table
    - Writes processed values to DuckDB processed_measurements table
    - Tracks last timestamp per signal for stale_check
    """
    def __init__(self, buffer=None):
        self.buffer = buffer
        self._profiles: dict[str, ProcessingProfile] = {}
        self._signal_profiles: dict[str, str] = {}  # signal_id → profile_id
        self._history: dict[str, list[float]] = defaultdict(list)
        self._last_timestamps: dict[str, datetime] = {}

        # Initialize DuckDB schema for raw + processed tables
        self._init_db_schema()

    def _init_db_schema(self):
        """Create raw_measurements and processed_measurements tables."""
        if not self.buffer:
            return
        try:
            conn = self.buffer.conn
            conn.execute("""
                CREATE TABLE IF NOT EXISTS raw_measurements (
                    ts          TIMESTAMPTZ NOT NULL,
                    signal_id   VARCHAR NOT NULL,
                    raw_value   DOUBLE,
                    source_ref  VARCHAR,
                    connector   VARCHAR,
                    quality_hint VARCHAR
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS processed_measurements (
                    ts          TIMESTAMPTZ NOT NULL,
                    signal_id   VARCHAR NOT NULL,
                    value       DOUBLE,
                    quality     VARCHAR,
                    source      VARCHAR,
                    profile_id  VARCHAR,
                    synced      BOOLEAN DEFAULT FALSE,
                    retry_count INTEGER DEFAULT 0
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_raw_signal_ts
                ON raw_measurements(signal_id, ts)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_proc_synced
                ON processed_measurements(synced, ts)
            """)
            logger.info("Initialized raw_measurements + processed_measurements tables")
        except Exception as e:
            logger.warning("Failed to init DB schema: %s", e)

    # ---- Profile management -------------------------------------------------

    def add_profile(self, profile: ProcessingProfile):
        """Add or update a processing profile."""
        self._profiles[profile.profile_id] = profile
        profile.updated_at = datetime.now(timezone.utc)
        if profile.created_at is None:
            profile.created_at = profile.updated_at

    def get_profile(self, profile_id: str) -> ProcessingProfile | None:
        return self._profiles.get(profile_id)

    def list_profiles(self) -> list[ProcessingProfile]:
        return list(self._profiles.values())

    def delete_profile(self, profile_id: str) -> bool:
        """Delete a profile. Returns False if signals are assigned to it."""
        if profile_id in self._signal_profiles.values():
            return False
        return self._profiles.pop(profile_id, None) is not None

    def assign_profile(self, signal_id: str, profile_id: str | None):
        """Assign a processing profile to a signal."""
        if profile_id is None:
            self._signal_profiles.pop(signal_id, None)
        else:
            self._signal_profiles[signal_id] = profile_id

    def get_profile_for_signal(self, signal_id: str) -> ProcessingProfile | None:
        profile_id = self._signal_profiles.get(signal_id)
        if profile_id:
            return self._profiles.get(profile_id)
        return None

    def list_signals_for_profile(self, profile_id: str) -> list[str]:
        return [sig for sig, pid in self._signal_profiles.items() if pid == profile_id]

    # ---- Pipeline execution -------------------------------------------------

    def apply(self, raw_value: float, profile: ProcessingProfile | None,
              signal_id: str = "", timestamp: datetime | None = None) -> ProcessedReading:
        """Apply processing pipeline to a raw value.

        Runs each step in order, propagating value and quality through the pipeline.
        Maintains per-signal history for moving average steps.
        """
        if not profile or not profile.steps:
            return ProcessedReading(
                signal_id=signal_id,
                value=raw_value,
                quality="GOOD",
                timestamp=timestamp or datetime.now(timezone.utc),
                profile_id=profile.profile_id if profile else None,
            )

        value = raw_value
        quality = "GOOD"
        warnings: list[str] = []
        now = timestamp or datetime.now(timezone.utc)
        history = self._history.get(signal_id, [])

        for step in sorted(profile.steps, key=lambda s: s.order):
            if not step.enabled:
                continue
            step_fn = STEP_REGISTRY.get(step.type)
            if not step_fn:
                logger.warning("Unknown step type: %s", step.type)
                continue

            try:
                # Special handling for stale_check which needs timestamp
                if step.type == "stale_check":
                    value, quality, step_warnings = step_fn(
                        value, quality, step.params, history,
                        timestamp=now,
                    )
                else:
                    value, quality, step_warnings = step_fn(
                        value, quality, step.params, history,
                    )
                warnings.extend(step_warnings)
            except Exception as e:
                logger.warning("Step %s failed: %s", step.type, e)
                quality = "BAD"
                warnings.append(f"Step '{step.type}' failed: {e}")

        # Update history
        self._history[signal_id].append(value)
        if len(self._history[signal_id]) > MAX_HISTORY:
            self._history[signal_id] = self._history[signal_id][-MAX_HISTORY:]
        self._last_timestamps[signal_id] = now

        return ProcessedReading(
            signal_id=signal_id,
            value=value,
            quality=quality,
            timestamp=now,
            profile_id=profile.profile_id if profile else None,
        )

    # ---- Preview (step-by-step) ---------------------------------------------

    def preview(self, raw_samples: list[float],
                profile: ProcessingProfile) -> dict[str, Any]:
        """Preview processing pipeline step-by-step with sample data.

        Returns detailed output per step + final values for each sample.
        """
        results: list[dict] = []
        final_values: list[float] = []
        final_qualities: list[str] = []
        all_warnings: list[str] = []

        for sample_idx, sample in enumerate(raw_samples):
            value = sample
            quality = "GOOD"
            step_outputs: list[dict] = []
            temp_history: list[float] = []

            for step in sorted(profile.steps, key=lambda s: s.order):
                if not step.enabled:
                    continue
                step_fn = STEP_REGISTRY.get(step.type)
                if not step_fn:
                    continue

                try:
                    ts = datetime.now(timezone.utc)
                    if step.type == "stale_check":
                        new_val, new_qual, sw = step_fn(
                            value, quality, step.params, temp_history, timestamp=ts,
                        )
                    else:
                        new_val, new_qual, sw = step_fn(
                            value, quality, step.params, temp_history,
                        )

                    step_outputs.append({
                        "step_type": step.type,
                        "order": step.order,
                        "input_value": value,
                        "output_value": new_val,
                        "input_quality": quality,
                        "output_quality": new_qual,
                        "warnings": sw,
                    })
                    value, quality = new_val, new_qual
                    all_warnings.extend(sw)
                except Exception as e:
                    step_outputs.append({
                        "step_type": step.type,
                        "order": step.order,
                        "input_value": value,
                        "output_value": value,
                        "input_quality": quality,
                        "output_quality": "BAD",
                        "warnings": [f"Error: {e}"],
                    })
                    quality = "BAD"

            temp_history.append(value)
            results.append({
                "sample_index": sample_idx,
                "raw_value": sample,
                "steps": step_outputs,
            })
            final_values.append(value)
            final_qualities.append(quality)

        return {
            "samples": results,
            "final_values": final_values,
            "final_qualities": final_qualities,
            "warnings": list(set(all_warnings)),
            "profile_id": profile.profile_id,
            "step_count": len(profile.steps),
        }

    # ---- DuckDB storage -----------------------------------------------------

    def write_raw(self, signal_id: str, raw_value: float, source_ref: str = "",
                  connector: str = "", quality_hint: str = "GOOD",
                  timestamp: datetime | None = None):
        """Write raw measurement to raw_measurements table."""
        if not self.buffer:
            return
        ts = timestamp or datetime.now(timezone.utc)
        try:
            self.buffer.conn.execute("""
                INSERT INTO raw_measurements (ts, signal_id, raw_value, source_ref, connector, quality_hint)
                VALUES (?, ?, ?, ?, ?, ?)
            """, [ts, signal_id, raw_value, source_ref, connector, quality_hint])
        except Exception as e:
            logger.warning("Failed to write raw measurement: %s", e)

    def write_processed(self, reading: ProcessedReading, source: str = "edge-v2"):
        """Write processed measurement to processed_measurements table."""
        if not self.buffer:
            return
        try:
            self.buffer.conn.execute("""
                INSERT INTO processed_measurements (ts, signal_id, value, quality, source, profile_id, synced)
                VALUES (?, ?, ?, ?, ?, ?, FALSE)
            """, [reading.timestamp, reading.signal_id, reading.value,
                  reading.quality, source, reading.profile_id])
        except Exception as e:
            logger.warning("Failed to write processed measurement: %s", e)

    def get_processed_unsynced(self, limit: int = 1000, max_retries: int = 3) -> list[dict]:
        """Get processed measurements not yet synced to Center."""
        if not self.buffer:
            return []
        rows = self.buffer.conn.execute("""
            SELECT ts, signal_id, value, quality, source, profile_id, retry_count
            FROM processed_measurements
            WHERE synced = FALSE AND retry_count < ?
            ORDER BY ts ASC LIMIT ?
        """, [max_retries, limit]).fetchall()
        return [
            {"timestamp": r[0].isoformat(), "signal_id": r[1], "value": r[2],
             "quality": r[3], "source": r[4], "profile_id": r[5], "retry_count": r[6]}
            for r in rows
        ]

    def mark_processed_synced(self, count: int):
        """Mark oldest N unsynced processed rows as synced."""
        if not self.buffer:
            return
        self.buffer.conn.execute("""
            UPDATE processed_measurements SET synced = TRUE
            WHERE rowid IN (
                SELECT rowid FROM processed_measurements WHERE synced = FALSE
                ORDER BY ts ASC LIMIT ?
            )
        """, [count])

    def get_processed_backlog(self) -> int:
        """Count unsynced processed measurements."""
        if not self.buffer:
            return 0
        row = self.buffer.conn.execute("""
            SELECT COUNT(*) FROM processed_measurements WHERE synced = FALSE
        """).fetchone()
        return row[0] if row else 0
