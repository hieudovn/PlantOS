"""Config backup/restore API routes — backup, restore, version, healthcheck."""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from aiohttp import web

logger = logging.getLogger(__name__)

BACKUP_DIR_NAME = "backups"


def register_backup_routes(app: web.Application, config):
    """Register config backup/restore and version routes."""

    backup_dir = config.config_path.parent / BACKUP_DIR_NAME
    backup_dir.mkdir(exist_ok=True)

    # ---- POST /api/config/backup — create timestamped backup -----------------
    async def backup_config(request: web.Request) -> web.Response:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        backup_path = backup_dir / f"config_backup_{timestamp}.yaml"

        import shutil
        shutil.copy2(config.config_path, backup_path)

        return web.json_response({
            "status": "backup_created",
            "path": str(backup_path),
            "timestamp": timestamp,
        })

    # ---- POST /api/config/restore — restore from backup ----------------------
    async def restore_config(request: web.Request) -> web.Response:
        try:
            body = await request.json()
        except Exception:
            return web.json_response({"error": "Invalid JSON"}, status=400)

        backup_file = body.get("path", "")
        backup_path = Path(backup_file)

        if not backup_path.exists():
            return web.json_response({"error": f"Backup file not found: {backup_file}"}, status=404)

        # Validate backup is valid YAML
        try:
            import yaml
            with open(backup_path) as f:
                yaml.safe_load(f)
        except Exception as e:
            return web.json_response({"error": f"Invalid backup file: {e}"}, status=400)

        # Create backup of current config before restoring
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        pre_restore = backup_dir / f"pre_restore_{timestamp}.yaml"
        import shutil
        shutil.copy2(config.config_path, pre_restore)

        # Restore backup
        shutil.copy2(backup_path, config.config_path)
        config._load()

        return web.json_response({
            "status": "restored",
            "backup_used": backup_file,
            "pre_restore_backup": str(pre_restore),
        })

    # ---- GET /api/config/backups — list available backups --------------------
    async def list_backups(request: web.Request) -> web.Response:
        backups = sorted(backup_dir.glob("*.yaml"), reverse=True)
        return web.json_response([
            {
                "path": str(b),
                "filename": b.name,
                "size_bytes": b.stat().st_size,
                "modified_at": datetime.fromtimestamp(b.stat().st_mtime, tz=timezone.utc).isoformat(),
            }
            for b in backups
        ])

    # ---- GET /api/version — version info ------------------------------------
    async def get_version(request: web.Request) -> web.Response:
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

        return web.json_response({
            "version": "2.0.0-dev",
            "build_date": "2026-07-08",
            "edge_node_id": config.edge_node_id,
            "plant_id": config.plant_id,
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "dependencies": deps,
        })

    app.router.add_post("/api/config/backup", backup_config)
    app.router.add_post("/api/config/restore", restore_config)
    app.router.add_get("/api/config/backups", list_backups)
    app.router.add_get("/api/version", get_version)
