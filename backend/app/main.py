"""PlantOS Center Backend — FastAPI Application."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import settings
from app.db import get_engine, dispose_engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle."""
    # Startup — initialize DB engine
    get_engine()
    yield
    # Shutdown — dispose DB engine
    dispose_engine()


app = FastAPI(
    title="PlantOS API",
    version=settings.APP_VERSION,
    lifespan=lifespan,
)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
    }
