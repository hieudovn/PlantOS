"""Signal Registry — FastAPI router."""

from fastapi import APIRouter, HTTPException, Query

from app.modules.signals.schemas import (
    SignalCreate,
    SignalUpdate,
    SignalResponse,
)
from app.modules.signals.service import SignalService

router = APIRouter()
signal_service = SignalService()


@router.post("/signals", response_model=SignalResponse, status_code=201)
def create_signal(data: SignalCreate):
    try:
        return signal_service.create_signal(data)
    except ValueError as e:
        raise HTTPException(
            status_code=409 if "already" in str(e) else 404, detail=str(e)
        )


@router.get("/signals", response_model=list[SignalResponse])
def list_signals(
    asset_id: str | None = Query(None),
    signal_type: str | None = Query(None),
    data_type: str | None = Query(None),
    plant_id: str | None = Query(None),
):
    return signal_service.list_signals(asset_id, signal_type, data_type, plant_id)


@router.get("/signals/{signal_id}", response_model=SignalResponse)
def get_signal(signal_id: str):
    try:
        return signal_service.get_signal(signal_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.patch("/signals/{signal_id}", response_model=SignalResponse)
def update_signal(signal_id: str, data: SignalUpdate):
    try:
        return signal_service.update_signal(signal_id, data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
