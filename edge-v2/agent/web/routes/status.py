"""Status API routes — health check, latest measurements."""

import logging

from aiohttp import web

logger = logging.getLogger(__name__)


def register_status_routes(app: web.Application, buffer, sync, health, config,
                            connectors, processing, auth=None):
    """Register status-related API routes."""

    # ---- GET /api/status — agent health + stats -----------------------------
    async def get_status(request: web.Request) -> web.Response:
        backlog = sync.get_backlog() if sync else 0
        signal_count = 0
        try:
            if buffer:
                rows = buffer.conn.execute(
                    "SELECT COUNT(*) FROM measurements"
                ).fetchone()
                signal_count = rows[0] if rows else 0
        except Exception:
            pass

        # DuckDB file size
        db_size = 0
        try:
            from pathlib import Path
            db_path = Path(buffer.path) if buffer else None
            if db_path and db_path.exists():
                db_size = db_path.stat().st_size
        except Exception:
            pass

        return web.json_response({
            "status": "running",
            "edge_node_id": config.edge_node_id,
            "plant_id": config.plant_id,
            "version": "2.0.0.dev",
            "uptime_seconds": 0,  # TODO: track in EdgeAgentV2
            "buffer": {
                "row_count": signal_count,
                "size_bytes": db_size,
                "retention_days": config.buffer_retention_days,
            },
            "sync": {
                "backlog": backlog,
                "interval_seconds": config.publish_interval,
                "batch_size": config.batch_size,
            },
            "connectors": {
                "active": connectors.active_count if connectors else 0,
            },
            "center": {
                "url": config.center_url,
            },
            "first_run": auth.is_first_run() if auth else False,
        })

    # ---- GET /api/measurements/latest — recent signal values -----------------
    async def get_latest_measurements(request: web.Request) -> web.Response:
        limit = int(request.query.get("limit", "20"))
        measurements = []
        try:
            if buffer:
                rows = buffer.conn.execute("""
                    SELECT ts, signal_id, value, quality
                    FROM measurements
                    ORDER BY ts DESC
                    LIMIT ?
                """, [limit]).fetchall()
                measurements = [
                    {"timestamp": r[0].isoformat(), "signal_id": r[1],
                     "value": r[2], "quality": r[3]}
                    for r in rows
                ]
        except Exception:
            pass
        return web.json_response(measurements)

    app.router.add_get("/api/status", get_status)
    app.router.add_get("/api/measurements/latest", get_latest_measurements)
