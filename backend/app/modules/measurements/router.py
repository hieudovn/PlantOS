"""Measurement API — FastAPI router."""

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


# Cached historian adapter singleton across requests
_historian_instance: HistorianInterface | None = None


def get_historian() -> HistorianInterface:
    """Provide a historian adapter instance (cached singleton).

    Tries TDengine first; falls back to Stub.
    Replace this with proper DI later.
    """
    global _historian_instance
    if _historian_instance is not None:
        return _historian_instance

    try:
        from app.modules.historian.tdengine_adapter import TDengineHistorianAdapter

        _historian_instance = TDengineHistorianAdapter()
    except ImportError:
        _historian_instance = StubHistorianAdapter()
    return _historian_instance


router = APIRouter()


@router.post("/measurements/ingest", response_model=IngestResponse)
async def ingest_measurements(
    data: IngestRequest,
    historian: HistorianInterface = Depends(get_historian),
):
    service = MeasurementService(historian)
    return await service.ingest(data)


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
