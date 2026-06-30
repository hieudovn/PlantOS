"""CDM Events — FastAPI CRUD router."""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from app.modules.events.schemas import (
    StateEventCreate,
    StateEventUpdate,
    StateEventResponse,
    DowntimeEventCreate,
    DowntimeEventUpdate,
    DowntimeEventResponse,
    ProductionEventCreate,
    ProductionEventResponse,
)
from app.modules.events.service import (
    StateEventService,
    DowntimeEventService,
    ProductionEventService,
)

router = APIRouter()


# ---- State Events ----

@router.post("/events/state", response_model=StateEventResponse, status_code=201)
async def create_state_event(data: StateEventCreate):
    """Record a state transition event."""
    return StateEventService.create(data)


@router.get("/events/state/{event_id}", response_model=StateEventResponse)
async def get_state_event(event_id: str):
    """Get a specific state event by ID."""
    event = StateEventService.get_by_id(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="State event not found")
    return event


@router.get("/events/state", response_model=dict)
async def list_state_events(
    asset_id: str = Query(..., description="Filter by asset ID"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    from_ts: Optional[str] = Query(None, alias="from"),
    to_ts: Optional[str] = Query(None, alias="to"),
):
    """List state events for an asset."""
    from_ = datetime.fromisoformat(from_ts) if from_ts else None
    to_ = datetime.fromisoformat(to_ts) if to_ts else None
    items, total = StateEventService.list_by_asset(
        asset_id, skip=skip, limit=limit, from_ts=from_, to_ts=to_
    )
    return {"items": items, "total": total}


# ---- Downtime Events ----

@router.post("/events/downtime", response_model=DowntimeEventResponse, status_code=201)
async def create_downtime_event(data: DowntimeEventCreate):
    """Record a downtime event."""
    return DowntimeEventService.create(data)


@router.patch("/events/downtime/{event_id}", response_model=DowntimeEventResponse)
async def update_downtime_event(event_id: str, data: DowntimeEventUpdate):
    """Update a downtime event (e.g., set ended_at on recovery)."""
    event = DowntimeEventService.update(event_id, data)
    if not event:
        raise HTTPException(status_code=404, detail="Downtime event not found")
    return event


@router.get("/events/downtime/{event_id}", response_model=DowntimeEventResponse)
async def get_downtime_event(event_id: str):
    """Get a specific downtime event by ID."""
    event = DowntimeEventService.get_by_id(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Downtime event not found")
    return event


@router.get("/events/downtime", response_model=dict)
async def list_downtime_events(
    asset_id: str = Query(..., description="Filter by asset ID"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    active_only: bool = Query(False, description="Only active (unresolved) events"),
):
    """List downtime events for an asset."""
    items, total = DowntimeEventService.list_by_asset(
        asset_id, skip=skip, limit=limit, active_only=active_only
    )
    return {"items": items, "total": total}


# ---- Production Events ----

@router.post("/events/production", response_model=ProductionEventResponse, status_code=201)
async def create_production_event(data: ProductionEventCreate):
    """Record a production event (count, batch, quality, rate)."""
    return ProductionEventService.create(data)


@router.get("/events/production/{event_id}", response_model=ProductionEventResponse)
async def get_production_event(event_id: str):
    """Get a specific production event by ID."""
    event = ProductionEventService.get_by_id(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Production event not found")
    return event


@router.get("/events/production", response_model=dict)
async def list_production_events(
    asset_id: str = Query(..., description="Filter by asset ID"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    event_type: Optional[str] = Query(None, description="Filter by event type"),
):
    """List production events for an asset."""
    items, total = ProductionEventService.list_by_asset(
        asset_id, skip=skip, limit=limit, event_type=event_type
    )
    return {"items": items, "total": total}
