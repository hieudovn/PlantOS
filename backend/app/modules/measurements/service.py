"""Measurement Service — ingestion + query via HistorianInterface."""

from app.db import get_session
from app.modules.historian.interface import HistorianInterface
from app.modules.historian.models import Measurement as HistorianMeasurement
from app.modules.historian.models import Quality as HistorianQuality
from app.modules.signals.repository import SignalRepository
from app.modules.assets.repository import AssetRepository
from app.modules.measurements.schemas import (
    IngestRequest,
    IngestResponse,
    CurrentValueResponse,
    HistoryQueryParams,
    HistoryResponse,
)


class MeasurementService:
    def __init__(self, historian: HistorianInterface):
        self.historian = historian

    async def ingest(self, data: IngestRequest) -> IngestResponse:
        """Validate signal_ids and write batch to historian."""
        # Validate all signal_ids exist
        with get_session() as session:
            signal_repo = SignalRepository(session)
            valid_ids = set()
            errors = []
            for m in data.measurements:
                signal = signal_repo.get_by_id(m.signal_id)
                if signal:
                    valid_ids.add(m.signal_id)
                else:
                    errors.append(f"Signal '{m.signal_id}' not found")

        # Convert to historian Measurement objects (only valid signals)
        historian_measurements = [
            HistorianMeasurement(
                timestamp=m.timestamp,
                signal_id=m.signal_id,
                value=m.value,
                quality=HistorianQuality(m.quality),
                source=data.source,
            )
            for m in data.measurements
            if m.signal_id in valid_ids
        ]

        # Write to historian
        result = await self.historian.write_measurements(historian_measurements)
        result.errors.extend(errors)
        result.rejected += len(errors)
        return IngestResponse(
            accepted=result.accepted,
            rejected=result.rejected,
            errors=result.errors,
        )

    async def get_current(
        self, asset_id: str | None = None, signal_id: str | None = None
    ) -> list[CurrentValueResponse]:
        """Get current (latest) values. Filter by asset_id or signal_id."""
        # Resolve signal_ids
        signal_ids = []
        with get_session() as session:
            if signal_id:
                signal_ids = [signal_id]
            elif asset_id:
                asset_repo = AssetRepository(session)
                asset = asset_repo.get_by_id(asset_id)
                if not asset:
                    return []
                signal_ids = [s.signal_id for s in asset.signals]
            else:
                return []  # Must provide asset_id or signal_id

        # Query historian
        latest_map = await self.historian.query_latest(signal_ids)

        # Build response
        results = []
        for sid in signal_ids:
            m = latest_map.get(sid)
            with get_session() as session:
                signal_repo = SignalRepository(session)
                signal = signal_repo.get_by_id(sid)
                asset_id_val = signal.asset.asset_id if signal else None

            results.append(
                CurrentValueResponse(
                    signal_id=sid,
                    asset_id=asset_id_val,
                    timestamp=m.timestamp if m else None,
                    value=m.value if m else None,
                    quality=m.quality.value if m and m.quality else None,
                    source=m.source if m else None,
                )
            )
        return results

    async def get_history(self, params: HistoryQueryParams) -> HistoryResponse:
        """Get historical data for a signal."""
        measurements = await self.historian.query_history(
            signal_id=params.signal_id,
            from_ts=params.from_ts,
            to_ts=params.to_ts,
            interval=params.interval,
        )
        data = [
            CurrentValueResponse(
                signal_id=m.signal_id,
                timestamp=m.timestamp,
                value=m.value,
                quality=m.quality.value if m.quality else None,
                source=m.source,
            )
            for m in measurements
        ]
        return HistoryResponse(signal_id=params.signal_id, data=data)
