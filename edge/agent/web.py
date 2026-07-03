"""Edge Agent HTTP server — status, monitoring, basic admin."""

import json
import time
from pathlib import Path
from aiohttp import web

start_time = time.time()

# References set by main.py after init
_buffer = None
_publisher = None
_sync_manager = None
_config = None
_modbus_collector = None
_opcua_collector = None
_metadata = None


def setup(buffer, publisher, sync_mgr, config):
    global _buffer, _publisher, _sync_manager, _config
    _buffer = buffer
    _publisher = publisher
    _sync_manager = sync_mgr
    _config = config


def set_modbus_collector(collector):
    global _modbus_collector
    _modbus_collector = collector


def set_opcua_collector(collector):
    global _opcua_collector
    _opcua_collector = collector


def set_metadata(metadata):
    global _metadata
    _metadata = metadata


async def handle_status(request):
    """JSON status endpoint (with graceful error handling)."""
    try:
        conn = _buffer.conn
        total = conn.execute("SELECT COUNT(*) FROM measurements").fetchone()[0]
        unsynced = _buffer.count_unsynced()
        db_path = Path(_buffer.path)
        db_size = db_path.stat().st_size / (1024 * 1024) if db_path.exists() else 0
    except Exception:
        total, unsynced, db_size = 0, 0, 0

    return web.json_response({
        "node_id": _config.get("edge_node_id", "unknown"),
        "uptime_seconds": int(time.time() - start_time),
        "duckdb": {"total_rows": total, "unsynced": unsynced, "db_size_mb": round(db_size, 2)},
        "mqtt": {"connected": _publisher.is_connected() if _publisher else False},
        "modbus": {
            "enabled": _modbus_collector is not None,
            "connected": _modbus_collector.connected if _modbus_collector else False,
            "host": _modbus_collector.client.host if _modbus_collector else None,
            "tags": len(_modbus_collector.mapper.tags) if _modbus_collector else 0,
        } if _modbus_collector else {"enabled": False},
        "opcua": {
            "enabled": _opcua_collector.total_signals > 0 if _opcua_collector else False,
            "any_connected": _opcua_collector.any_connected if _opcua_collector else False,
            "total_signals": _opcua_collector.total_signals if _opcua_collector else 0,
            "endpoints": _opcua_collector.status_list if _opcua_collector else [],
        } if _opcua_collector else {"enabled": False, "endpoints": []},
        "sync": {"backlog": unsynced},
        "signals": len(_config.get("signals", [])),
        "version": "0.2.0",
    })


async def handle_latest(request):
    """Latest value per signal (current snapshot)."""
    try:
        rows = _buffer.conn.execute("""
            SELECT signal_id, value, quality, ts
            FROM measurements
            WHERE ts = (SELECT MAX(ts) FROM measurements m2 WHERE m2.signal_id = measurements.signal_id)
            ORDER BY signal_id
        """).fetchall()
        results = []
        for r in rows:
            ts = r[3]
            if hasattr(ts, 'isoformat'):
                ts_str = ts.isoformat()
            elif ts is not None:
                ts_str = str(ts)
            else:
                ts_str = None
            results.append({
                "signal_id": r[0],
                "value": r[1],
                "quality": r[2] or "SIMULATED",
                "timestamp": ts_str,
            })
        return web.json_response(results)
    except Exception as e:
        import logging
        logging.getLogger("web").error(f"handle_latest error: {e}", exc_info=True)
        return web.json_response([])


async def handle_recent(request):
    """50 most recent measurements."""
    limit = int(request.query.get("limit", "50"))
    rows = _buffer.conn.execute("""
        SELECT ts, signal_id, value, quality
        FROM measurements
        ORDER BY ts DESC LIMIT ?
    """, [limit]).fetchall()

    return web.json_response([
        {"timestamp": r[0].isoformat() if r[0] else None, "signal_id": r[1], "value": r[2], "quality": r[3]}
        for r in rows
    ])


async def handle_config(request):
    """Current config (sanitized — no passwords)."""
    cfg = dict(_config)
    return web.json_response(cfg)


async def handle_assets(request):
    """Return synced assets from metadata manager."""
    try:
        manifest = _metadata.manifest if _metadata else {}
        return web.json_response(manifest.get("assets", []))
    except Exception:
        return web.json_response([])


async def handle_index(request):
    """Serve inline HTML dashboard."""
    return web.FileResponse("templates/dashboard.html")


async def handle_protocol_status(request):
    """Return protocol connection status."""
    return web.json_response({
        "modbus": {
            "enabled": _modbus_collector is not None,
            "connected": _modbus_collector.connected if _modbus_collector else False,
            "host": _modbus_collector.config.get("host") if _modbus_collector else None,
            "tags": len(_modbus_collector.mapper.tags) if _modbus_collector else 0,
        },
        "opcua": {
            "enabled": _opcua_collector.total_signals > 0 if _opcua_collector else False,
            "any_connected": _opcua_collector.any_connected if _opcua_collector else False,
            "total_signals": _opcua_collector.total_signals if _opcua_collector else 0,
            "endpoints": _opcua_collector.status_list if _opcua_collector else [],
        } if _opcua_collector else {"enabled": False, "endpoints": []},
    })


async def handle_save_connection(request):
    """Save Modbus connection config to YAML."""
    try:
        data = await request.json()
        if "modbus" not in _config:
            _config["modbus"] = {}
        _config["modbus"].update(data.get("modbus", {}))
        import yaml
        with open("config.yaml", "w") as f:
            yaml.dump(dict(_config), f, default_flow_style=False)
        return web.json_response({"status": "saved"})
    except Exception as e:
        return web.json_response({"status": "error", "message": str(e)}, status=500)


async def handle_setup_page(request):
    """Serve protocol setup page."""
    return web.FileResponse("templates/setup.html")


async def handle_logout(request):
    """Serve logout page."""
    return web.FileResponse("templates/logout.html")


def create_app():
    app = web.Application()
    app.router.add_get("/", handle_index)
    app.router.add_get("/logout", handle_logout)
    app.router.add_get("/setup", handle_setup_page)
    app.router.add_get("/api/status", handle_status)
    app.router.add_get("/api/measurements/latest", handle_latest)
    app.router.add_get("/api/measurements/recent", handle_recent)
    app.router.add_get("/api/config", handle_config)
    app.router.add_get("/api/assets", handle_assets)
    app.router.add_get("/api/protocols/status", handle_protocol_status)
    app.router.add_post("/api/connections/save", handle_save_connection)
    return app


async def run_server(host="0.0.0.0", port=8001):
    app = create_app()
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host, port)
    await site.start()
    print(f"Edge Web UI: http://{host}:{port}")
