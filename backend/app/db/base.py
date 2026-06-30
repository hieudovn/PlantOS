"""SQLAlchemy base, engine, and session management."""

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings


class Base(DeclarativeBase):
    """Base class for all PlantOS SQLAlchemy models."""
    pass


# Engine is created lazily to avoid import-time DB connection
_engine = None
_SessionLocal = None


def get_engine():
    """Return (or create) the SQLAlchemy engine."""
    global _engine
    if _engine is None:
        _engine = create_engine(
            settings.DATABASE_URL,
            echo=settings.DEBUG,
            pool_size=5,
            max_overflow=10,
        )
    return _engine


def get_session():
    """Return a new SQLAlchemy session."""
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(bind=get_engine())
    return _SessionLocal()


def dispose_engine():
    """Dispose the engine (for graceful shutdown)."""
    global _engine, _SessionLocal
    if _engine is not None:
        _engine.dispose()
        _engine = None
        _SessionLocal = None
