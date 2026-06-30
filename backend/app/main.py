"""PlantOS Center Backend — FastAPI Application."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import v1_router
from app.core.config import settings
from app.db import get_engine, dispose_engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle."""
    # Startup — initialize DB engine
    get_engine()

    # Connect historian adapter if TDengine is available
    historian_adapter = None
    try:
        from app.modules.historian.tdengine_adapter import TDengineHistorianAdapter
        import app.modules.measurements.router as mr

        adapter = TDengineHistorianAdapter()
        ok = await adapter.connect()
        if ok:
            mr._historian_instance = adapter
            historian_adapter = adapter
            print(f"Historian connected: TDengine at {settings.TDENGINE_HOST}")
        else:
            print("Historian: TDengine unavailable, using Stub")
    except Exception as e:
        print(f"Historian init skipped: {e}")

    yield

    # Shutdown
    if historian_adapter is not None and hasattr(historian_adapter, "close"):
        await historian_adapter.close()
    dispose_engine()


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

app.include_router(v1_router)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
    }
