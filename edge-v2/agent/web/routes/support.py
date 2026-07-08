"""Support bundle API route — downloads sanitized ZIP with diagnostics."""

import io
import json
import logging
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from aiohttp import web

logger = logging.getLogger(__name__)


def _sanitize_config(config) -> dict:
    """Return sanitized config with secrets redacted."""
    SECRET_KEYS = {"api_key", "password", "secret", "hash", "token",
                   "admin_hash", "session_secret", "session_secret_ref",
                   "password_secret_ref"}

    def _redact(obj, parent_key=""):
        if isinstance(obj, dict):
            return {
                k: "***REDACTED***"
                if any(secret in k.lower() for secret in SECRET_KEYS)
                else _redact(v, k)
                for k, v in obj.items()
            }
        if isinstance(obj, list):
            return [_redact(v, parent_key) for v in obj]
        return obj

    raw = getattr(config, "_data", {})
    return _redact(raw)


def register_support_routes(app: web.Application, config, connectors,
                             buffer, processing):
    """Register support bundle and diagnostics routes."""

    # ---- GET /api/support/bundle — download support ZIP ----------------------
    async def get_support_bundle(request: web.Request) -> web.Response:
        buf = io.BytesIO()

        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            # 1. Sanitized config
            zf.writestr("config_sanitized.json",
                        json.dumps(_sanitize_config(config), indent=2))

            # 2. Version info
            import sys
            deps = {}
            try:
                import duckdb
                deps["duckdb"] = duckdb.__version__
            except Exception:
                deps["duckdb"] = "?"
            try:
                import aiohttp
                deps["aiohttp"] = aiohttp.__version__
            except Exception:
                deps["aiohttp"] = "?"
            zf.writestr("version.json", json.dumps({
                "version": "2.0.0-dev",
                "build_date": "2026-07-08",
                "edge_node_id": config.edge_node_id,
                "plant_id": config.plant_id,
                "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
                "dependencies": deps,
                "generated_at": datetime.now(timezone.utc).isoformat(),
            }, indent=2))

            # 3. Connector status snapshot
            connector_status = []
            if connectors:
                try:
                    connector_status = connectors.list_status_sync()
                except Exception:
                    pass
            zf.writestr("connectors.json",
                        json.dumps(connector_status, indent=2))

            # 4. Metrics snapshot
            metrics = {
                "buffer": {"row_count": 0, "size_bytes": 0},
                "sync": {"backlog": 0},
                "processing": {"profiles": 0},
            }
            if buffer:
                try:
                    rows = buffer.conn.execute(
                        "SELECT COUNT(*) FROM measurements"
                    ).fetchone()
                    metrics["buffer"]["row_count"] = rows[0] if rows else 0
                    db_path = Path(buffer.path)
                    if db_path.exists():
                        metrics["buffer"]["size_bytes"] = db_path.stat().st_size
                except Exception:
                    pass
            if hasattr(config, "publish_interval"):
                metrics["sync"]["backlog"] = 0
            if processing:
                metrics["processing"]["profiles"] = len(processing.list_profiles())
            zf.writestr("metrics.json", json.dumps(metrics, indent=2))

            # 5. Recent log entries (last 100 lines from memory if available)
            zf.writestr("notes.txt",
                        "Support Bundle — PlantOS Edge Lite v2\n"
                        f"Generated: {datetime.now(timezone.utc).isoformat()}\n"
                        f"Node: {config.edge_node_id}\n"
                        f"Plant: {config.plant_id}\n"
                        "\n"
                        "System logs: journalctl -u plantos-edge-v2 -n 100 --no-pager\n"
                        "Docker logs: docker logs plantos-edge-v2 --tail 100\n")

        buf.seek(0)
        return web.Response(
            body=buf.getvalue(),
            content_type="application/zip",
            headers={
                "Content-Disposition": f'attachment; filename="plantos-edge-support-{datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")}.zip"',
            },
        )

    app.router.add_get("/api/support/bundle", get_support_bundle)
