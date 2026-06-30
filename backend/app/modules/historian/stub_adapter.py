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
