"""PlantOS Center Backend — FastAPI Application."""

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import v1_router
from app.api.ws import router as ws_router, broadcast_measurements
from app.core.config import settings
from app.core.events import subscribe
from app.db import get_engine, dispose_engine
from app.middleware.auth import AuthMiddleware
from app.modules.auth.router import router as auth_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle."""
    # Startup — initialize DB engine
    get_engine()

    # Register EventDispatcher subscribers
    _register_event_subscribers()

    yield
    # Shutdown — dispose DB engine
    dispose_engine()


def _register_event_subscribers():
    """Register side-effect handlers for internal events.

    Subscribers run in-process when events are dispatched.
    Each runs independently — a failure in one does not affect others.
    """
    from app.modules.alarms.calculator import SignalCalculator
    from app.modules.alarms.service import AlarmEvaluator
    from app.modules.historian.stub_adapter import StubHistorianAdapter
    from app.modules.events.subscribers import on_edge_heartbeat

    async def _broadcast_handler(data: dict):
        measurements = data.get("measurements", [])
        if measurements:
            await broadcast_measurements(measurements)

    async def _alarm_eval_handler(data: dict):
        measurements = data.get("measurements", [])
        if measurements:
            evaluator = AlarmEvaluator()
            await evaluator.evaluate(measurements)

    async def _calc_eval_handler(data: dict):
        measurements = data.get("measurements", [])
        if measurements:
            historian = StubHistorianAdapter()
            calc = SignalCalculator(historian)
            await calc.evaluate(measurements)

    subscribe("measurements.ingested", _broadcast_handler)
    subscribe("measurements.ingested", _alarm_eval_handler)
    subscribe("measurements.ingested", _calc_eval_handler)
    subscribe("edge.heartbeat", on_edge_heartbeat)
    logger.info("EventDispatcher subscribers registered for 'measurements.ingested' and 'edge.heartbeat'")


app = FastAPI(
    title="PlantOS API",
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Auth middleware — protects all /api/v1/* routes except /auth/login
app.add_middleware(AuthMiddleware)

app.include_router(auth_router, prefix="/api/v1", tags=["Auth"])
app.include_router(v1_router)
app.include_router(ws_router)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
    }


@app.get("/api/v1/historian/health")
async def historian_health():
    """Historian backend health check."""
    try:
        from app.modules.historian.tdengine_adapter import TDengineHistorianAdapter

        adapter = TDengineHistorianAdapter()
        ok = await adapter.connect()
        if ok:
            await adapter.close()
            return {"status": "healthy", "backend": "tdengine"}
    except Exception:
        pass

    return {"status": "unhealthy", "backend": "unavailable"}
