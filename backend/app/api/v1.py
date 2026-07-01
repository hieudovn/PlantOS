"""API v1 router — aggregates all module routers."""

from fastapi import APIRouter

from app.modules.assets.router import router as assets_router
from app.modules.signals.router import router as signals_router
from app.modules.measurements.router import router as measurements_router
from app.modules.edge_nodes.router import router as edge_nodes_router
from app.modules.alarms.router import router as alarms_router
from app.modules.events.router import router as events_router
from app.modules.system.router import router as system_router
from app.modules.contracts.router import router as contracts_router

router = APIRouter(prefix="/api/v1")
router.include_router(assets_router, tags=["Assets"])
router.include_router(signals_router, tags=["Signals"])
router.include_router(measurements_router, tags=["Measurements"])
router.include_router(edge_nodes_router, tags=["Edge Nodes"])
router.include_router(alarms_router, tags=["Alarms"])
router.include_router(events_router, tags=["Events"])
router.include_router(system_router, tags=["System"])
router.include_router(contracts_router, tags=["Contracts"])


# ---- Seed endpoint (idempotent) ----

@router.post("/seed/vf-demo", tags=["Seed"])
def seed_vf_demo():
    """Seed Virtual Factory Compressor Train plant assets and signals."""
    from app.seed.vf_demo_plant import seed_vf_demo_plant
    try:
        results = seed_vf_demo_plant()
        return {"status": "ok", **results}
    except Exception as e:
        return {"status": "error", "message": str(e)}
