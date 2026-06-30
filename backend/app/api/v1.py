"""API v1 router — aggregates all module routers."""

from fastapi import APIRouter

from app.modules.assets.router import router as assets_router
from app.modules.signals.router import router as signals_router
from app.modules.measurements.router import router as measurements_router

router = APIRouter(prefix="/api/v1")
router.include_router(assets_router, tags=["Assets"])
router.include_router(signals_router, tags=["Signals"])
router.include_router(measurements_router, tags=["Measurements"])
