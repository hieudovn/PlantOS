"""Measurement API — FastAPI router."""

import asyncio
from fastapi import APIRouter, HTTPException, Query, Depends

from app.modules.historian.interface import HistorianInterface
from app.modules.historian.stub_adapter import StubHistorianAdapter
from app.modules.measurements.schemas import (
    IngestRequest,
    IngestResponse,
    CurrentValueResponse,
    HistoryQueryParams,
    HistoryResponse,
)
from app.modules.measurements.service import MeasurementService


_historian_instance: HistorianInterface | None = None


async def get_historian() -> HistorianInterface:
    """Async dependency — connect TDengine on first call, cache singleton.

    Tries TDengine first; falls back to Stub if unavailable.
    FastAPI supports async dependency functions natively.
    """
    global _historian_instance
    if _historian_instance is not None:
        return _historian_instance

    try:
        from app.modules.historian.tdengine_adapter import TDengineHistorianAdapter

        adapter = TDengineHistorianAdapter()
        ok = await adapter.connect()
        if ok:
            _historian_instance = adapter
            return adapter
    except Exception:
        pass

    _historian_instance = StubHistorianAdapter()
    return _historian_instance


router = APIRouter()


@router.post("/measurements/ingest", response_model=IngestResponse)
async def ingest_measurements(
    data: IngestRequest,
    historian: HistorianInterface = Depends(get_historian),
):
    service = MeasurementService(historian)
    result = await service.ingest(data)

    # Broadcast accepted measurements via WebSocket (non-blocking)
    if result.accepted > 0:
        from app.api.ws import broadcast_measurements

        ws_data = [
            {
                "timestamp": m.timestamp.isoformat() if hasattr(m, "timestamp") else m["timestamp"],
                "signal_id": m.signal_id if hasattr(m, "signal_id") else m["signal_id"],
                "value": m.value if hasattr(m, "value") else m["value"],
                "quality": m.quality if hasattr(m, "quality") else m.get("quality", "GOOD"),
            }
            for m in data.measurements
        ]
        asyncio.create_task(broadcast_measurements(ws_data))

        # Trigger alarm rule evaluation (non-blocking)
        from app.modules.alarms.service import AlarmEvaluator

        evaluator = AlarmEvaluator()
        asyncio.create_task(evaluator.evaluate(ws_data))

        # Trigger calculated signal evaluation (non-blocking)
        from app.modules.alarms.calculator import SignalCalculator

        calc = SignalCalculator(historian)
        asyncio.create_task(calc.evaluate(ws_data))

    return result


@router.get("/measurements/current", response_model=list[CurrentValueResponse])
async def get_current_values(
    asset_id: str | None = Query(None),
    signal_id: str | None = Query(None),
    historian: HistorianInterface = Depends(get_historian),
):
    if not asset_id and not signal_id:
        raise HTTPException(
            status_code=400, detail="Provide asset_id or signal_id"
        )
    service = MeasurementService(historian)
    return await service.get_current(asset_id=asset_id, signal_id=signal_id)


@router.get("/measurements/history", response_model=HistoryResponse)
async def get_history(
    signal_id: str = Query(...),
    from_ts: str = Query(..., alias="from"),
    to_ts: str = Query(..., alias="to"),
    interval: str | None = Query(None),
    historian: HistorianInterface = Depends(get_historian),
):
    from datetime import datetime

    try:
        params = HistoryQueryParams(
            signal_id=signal_id,
            from_ts=datetime.fromisoformat(from_ts),
            to_ts=datetime.fromisoformat(to_ts),
            interval=interval,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=400, detail=f"Invalid timestamp: {e}"
        )
    service = MeasurementService(historian)
    return await service.get_history(params)
