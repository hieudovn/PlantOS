"""TDengine connection manager using taos-ws-py (WebSocket)."""

import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


def build_tdengine_dsn() -> str:
    """Build TDengine WebSocket DSN from settings."""
    return (
        f"taosws://{settings.TDENGINE_USER}:{settings.TDENGINE_PASSWORD}"
        f"@{settings.TDENGINE_HOST}:{settings.TDENGINE_PORT}"
    )


def create_tdengine_connection():
    """Create a sync TDengine WebSocket connection.

    Uses Cursor for DB-API 2.0 style query execution.
    Returns (connection, cursor) tuple.
    """
    from taosws import connect

    dsn = build_tdengine_dsn()
    conn = connect(dsn)
    cursor = conn.cursor()
    return conn, cursor


async def ensure_database(conn_cursor) -> bool:
    """Ensure the PlantOS database exists in TDengine.

    conn_cursor is a tuple (connection, cursor).
    Returns True if successful.
    """
    conn, cursor = conn_cursor
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {settings.TDENGINE_DATABASE} PRECISION 'ms' DURATION 30")
    cursor.execute(f"USE {settings.TDENGINE_DATABASE}")
    return True
