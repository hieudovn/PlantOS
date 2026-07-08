"""Connector API routes — safe apply lifecycle + tag management.

Endpoints implement the Draft → Validate → Test → Apply → Confirm → Rollback flow.
All config changes go through API (no direct YAML manipulation).
"""

import csv
import io
import json
import logging
from datetime import datetime, timezone

from aiohttp import web

from agent.connectors.base import TagConfig

logger = logging.getLogger(__name__)

CSRF_METHODS = {"POST", "PUT", "DELETE", "PATCH"}


def register_connection_routes(app: web.Application, config, registry):
    """Register all connector management API routes."""

    # ---- 2.6 GET /api/connections — list all connectors with status ----------
    async def list_connections(request: web.Request) -> web.Response:
        statuses = await registry.get_status_all()
        # Also include draft-only connectors not yet applied
        connectors_cfg = config.get("connectors", {})
        for conn_id, conn_cfg in connectors_cfg.items():
            if not any(s["connector_id"] == conn_id for s in statuses):
                statuses.append({
                    "connector_id": conn_id,
                    "type": conn_cfg.get("type", "unknown"),
                    "status": "configured",
                    "connected": False,
                    "signal_count": len(conn_cfg.get("tags", [])),
                    "last_error": None,
                    "last_error_at": None,
                })
        return web.json_response(statuses)

    # ---- 2.7 POST /api/connections — create draft connector config -----------
    async def create_connection(request: web.Request) -> web.Response:
        try:
            body = await request.json()
        except Exception:
            return web.json_response({"error": "Invalid JSON"}, status=400)

        conn_id = body.get("connector_id", "")
        if not conn_id:
            return web.json_response({"error": "Missing 'connector_id'"}, status=400)

        # Save as draft
        draft = {
            "type": body.get("type", ""),
            "connection": body.get("connection", {}),
            "tags": body.get("tags", []),
            "enabled": body.get("enabled", True),
            "poll_interval_ms": body.get("poll_interval_ms", 1000),
        }
        version = config.save_draft(f"connector_{conn_id}", draft)
        return web.json_response({
            "status": "draft_created",
            "connector_id": conn_id,
            "draft_version": version,
        })

    # ---- 2.8 GET /api/connections/{id} — get connector detail + config -------
    async def get_connection(request: web.Request) -> web.Response:
        conn_id = request.match_info.get("id", "")
        connectors_cfg = config.get("connectors", {})
        conn_cfg = connectors_cfg.get(conn_id, {})
        draft = config.get_draft(f"connector_{conn_id}")

        instance = registry.get(conn_id)
        status = None
        if instance:
            try:
                status = await instance.status()
            except Exception:
                pass

        return web.json_response({
            "connector_id": conn_id,
            "active_config": conn_cfg,
            "draft": draft,
            "status": {
                "connector_id": conn_id,
                "type": conn_cfg.get("type", ""),
                "status": status.status if status else "unconfigured",
                "connected": status.connected if status else False,
                "signal_count": status.signal_count if status else 0,
                "last_error": status.last_error if status else None,
            } if status or conn_cfg else None,
        })

    # ---- 2.9 PUT /api/connections/{id} — update draft config -----------------
    async def update_connection(request: web.Request) -> web.Response:
        conn_id = request.match_info.get("id", "")
        try:
            body = await request.json()
        except Exception:
            return web.json_response({"error": "Invalid JSON"}, status=400)

        existing = config.get_draft(f"connector_{conn_id}") or {}
        existing.update(body)
        version = config.save_draft(f"connector_{conn_id}", existing)
        return web.json_response({"status": "draft_updated", "draft_version": version})

    # ---- 2.10 POST /api/connections/{id}/validate — validate draft -----------
    async def validate_connection(request: web.Request) -> web.Response:
        conn_id = request.match_info.get("id", "")
        draft = config.get_draft(f"connector_{conn_id}")
        if not draft:
            return web.json_response({"error": "No draft found"}, status=404)

        # Generic schema validation
        errors = config.validate_draft(f"connector_{conn_id}")

        # Protocol-specific validation
        conn_type = draft.get("type", "")
        cls = CONNECTOR_REGISTRY.get(conn_type)
        if cls:
            instance = cls("__validate__", draft)
            proto_errors = await instance.validate_config(draft)
            errors.extend(proto_errors)

        return web.json_response({
            "valid": len(errors) == 0,
            "errors": errors,
        })

    # ---- 2.11 POST /api/connections/{id}/test — test connection --------------
    async def test_connection(request: web.Request) -> web.Response:
        conn_id = request.match_info.get("id", "")
        draft = config.get_draft(f"connector_{conn_id}")
        if not draft:
            return web.json_response({"error": "No draft found"}, status=404)

        conn_type = draft.get("type", "")
        cls = CONNECTOR_REGISTRY.get(conn_type)
        if not cls:
            return web.json_response({"error": f"Unknown connector type: {conn_type}"}, status=400)

        instance = cls("__test__", draft)
        result = await instance.test_connection()
        return web.json_response({
            "success": result.success,
            "message": result.message,
            "detail": result.detail,
            "latency_ms": result.latency_ms,
        })

    # ---- 2.12 POST /api/connections/{id}/apply — promote draft → active ------
    async def apply_connection(request: web.Request) -> web.Response:
        conn_id = request.match_info.get("id", "")
        draft = config.get_draft(f"connector_{conn_id}")
        if not draft:
            return web.json_response({"error": "No draft found"}, status=404)

        backup_key = config.apply_draft(f"connector_{conn_id}")
        if not backup_key:
            return web.json_response({"error": "Apply failed"}, status=500)

        # Update connectors section in config
        connectors = config._data.setdefault("connectors", {})
        connectors[conn_id] = dict(draft)
        config._save()

        # Restart the connector with new config
        old_instance = registry.get(conn_id)
        if old_instance:
            await old_instance.stop()

        conn_type = draft.get("type", "")
        cls = CONNECTOR_REGISTRY.get(conn_type)
        if cls:
            instance = cls(conn_id, draft)
            await registry.get_or_create(conn_id, draft)
            if draft.get("enabled", True):
                await instance.start()

        return web.json_response({
            "status": "applied",
            "connector_id": conn_id,
            "backup_key": backup_key,
            "waiting_confirm": True,
        })

    # ---- 2.13 POST /api/connections/{id}/confirm — confirm apply success -----
    async def confirm_connection(request: web.Request) -> web.Response:
        conn_id = request.match_info.get("id", "")
        try:
            body = await request.json()
        except Exception:
            body = {}
        success = body.get("success", True)
        config.confirm_apply(f"connector_{conn_id}", success)
        return web.json_response({"status": "confirmed" if success else "rolled_back"})

    # ---- 2.14 POST /api/connections/{id}/rollback — revert to previous --------
    async def rollback_connection(request: web.Request) -> web.Response:
        conn_id = request.match_info.get("id", "")
        config.rollback(f"connector_{conn_id}")

        # Restore from backup in config
        connectors = config._data.setdefault("connectors", {})
        backup_key = None
        if conn_id in connectors:
            draft = config.get_draft(f"connector_{conn_id}")
            if draft:
                connectors[conn_id] = dict(draft)
                config._save()

        # Restart connector with old config
        old_instance = registry.get(conn_id)
        if old_instance:
            await old_instance.stop()

        restored_cfg = connectors.get(conn_id, {})
        conn_type = restored_cfg.get("type", "")
        cls = CONNECTOR_REGISTRY.get(conn_type)
        if cls and restored_cfg:
            instance = cls(conn_id, restored_cfg)
            await registry.get_or_create(conn_id, restored_cfg)
            if restored_cfg.get("enabled", True):
                await instance.start()

        return web.json_response({"status": "rolled_back"})

    # ---- 2.15 POST /api/connections/{id}/start -------------------------------
    async def start_connector(request: web.Request) -> web.Response:
        conn_id = request.match_info.get("id", "")
        instance = registry.get(conn_id)
        if not instance:
            return web.json_response({"error": "Connector not found"}, status=404)
        await instance.start()
        return web.json_response({"status": "started"})

    # ---- 2.16 POST /api/connections/{id}/stop --------------------------------
    async def stop_connector(request: web.Request) -> web.Response:
        conn_id = request.match_info.get("id", "")
        instance = registry.get(conn_id)
        if not instance:
            return web.json_response({"error": "Connector not found"}, status=404)
        await instance.stop()
        return web.json_response({"status": "stopped"})

    # ---- 2.17 POST /api/connections/{id}/restart -----------------------------
    async def restart_connector(request: web.Request) -> web.Response:
        conn_id = request.match_info.get("id", "")
        instance = registry.get(conn_id)
        if not instance:
            return web.json_response({"error": "Connector not found"}, status=404)
        await instance.restart()
        return web.json_response({"status": "restarted"})

    # ---- 2.18 GET /api/connections/{id}/tags — list tag mappings -------------
    async def list_tags(request: web.Request) -> web.Response:
        conn_id = request.match_info.get("id", "")
        connectors_cfg = config.get("connectors", {})
        conn_cfg = connectors_cfg.get(conn_id, {})
        tags = conn_cfg.get("tags", [])
        return web.json_response(tags)

    # ---- 2.19 POST /api/connections/{id}/tags — add/update tag mapping -------
    async def add_tag(request: web.Request) -> web.Response:
        conn_id = request.match_info.get("id", "")
        try:
            body = await request.json()
        except Exception:
            return web.json_response({"error": "Invalid JSON"}, status=400)

        connectors = config._data.setdefault("connectors", {})
        conn_cfg = connectors.setdefault(conn_id, {})
        tags = conn_cfg.setdefault("tags", [])

        tag_id = body.get("tag_id", "")
        if tag_id:
            # Update existing
            for i, t in enumerate(tags):
                if t.get("tag_id") == tag_id:
                    tags[i] = body
                    break
            else:
                tags.append(body)
        else:
            body["tag_id"] = f"tag_{len(tags) + 1}"
            tags.append(body)

        config._save()
        return web.json_response({"status": "tag_saved", "tag": body})

    # ---- 2.20 DELETE /api/connections/{id}/tags/{tag_id} — remove tag --------
    async def delete_tag(request: web.Request) -> web.Response:
        conn_id = request.match_info.get("id", "")
        tag_id = request.match_info.get("tag_id", "")
        connectors = config._data.setdefault("connectors", {})
        conn_cfg = connectors.setdefault(conn_id, {})
        tags = conn_cfg.setdefault("tags", [])
        conn_cfg["tags"] = [t for t in tags if t.get("tag_id") != tag_id]
        config._save()
        return web.json_response({"status": "tag_deleted"})

    # ---- 2.21 POST /api/connections/{id}/tags/import — CSV import ------------
    async def import_tags_csv(request: web.Request) -> web.Response:
        conn_id = request.match_info.get("id", "")
        try:
            text = await request.text()
        except Exception:
            return web.json_response({"error": "Invalid request body"}, status=400)

        reader = csv.DictReader(io.StringIO(text))
        connectors = config._data.setdefault("connectors", {})
        conn_cfg = connectors.setdefault(conn_id, {})
        tags = conn_cfg.setdefault("tags", [])

        imported = 0
        for row in reader:
            tag = {
                "tag_id": row.get("tag_id", f"tag_{len(tags) + 1}"),
                "source_ref": row.get("source_ref", ""),
                "signal_id": row.get("signal_id", ""),
                "data_type": row.get("data_type", "float"),
                "scale": float(row.get("scale", 1.0)),
                "offset": float(row.get("offset", 0.0)),
                "enabled": row.get("enabled", "true").lower() == "true",
            }
            tags.append(tag)
            imported += 1

        config._save()
        return web.json_response({"status": "imported", "count": imported})

    # ---- 2.22 GET /api/connections/{id}/tags/export — CSV export -------------
    async def export_tags_csv(request: web.Request) -> web.Response:
        conn_id = request.match_info.get("id", "")
        connectors_cfg = config.get("connectors", {})
        conn_cfg = connectors_cfg.get(conn_id, {})
        tags = conn_cfg.get("tags", [])

        output = io.StringIO()
        if tags:
            writer = csv.DictWriter(output, fieldnames=tags[0].keys())
            writer.writeheader()
            writer.writerows(tags)
        csv_content = output.getvalue()

        return web.Response(
            body=csv_content,
            content_type="text/csv",
            headers={
                "Content-Disposition": f'attachment; filename="connector_{conn_id}_tags.csv"',
            },
        )

    # ---- 2.23 GET /api/connections/{id}/browse — browse OPC UA address space --
    async def browse_connection(request: web.Request) -> web.Response:
        conn_id = request.match_info.get("id", "")
        path = request.query.get("path", "i=84")
        instance = registry.get(conn_id)
        if not instance:
            return web.json_response({"error": "Connector not running"}, status=400)

        try:
            nodes = await instance.browse(path)
            return web.json_response(nodes)
        except Exception as e:
            return web.json_response({"error": str(e)}, status=500)

    # Register routes
    app.router.add_get("/api/connections", list_connections)
    app.router.add_post("/api/connections", create_connection)
    app.router.add_get("/api/connections/{id}", get_connection)
    app.router.add_put("/api/connections/{id}", update_connection)
    app.router.add_post("/api/connections/{id}/validate", validate_connection)
    app.router.add_post("/api/connections/{id}/test", test_connection)
    app.router.add_post("/api/connections/{id}/apply", apply_connection)
    app.router.add_post("/api/connections/{id}/confirm", confirm_connection)
    app.router.add_post("/api/connections/{id}/rollback", rollback_connection)
    app.router.add_post("/api/connections/{id}/start", start_connector)
    app.router.add_post("/api/connections/{id}/stop", stop_connector)
    app.router.add_post("/api/connections/{id}/restart", restart_connector)
    app.router.add_get("/api/connections/{id}/tags", list_tags)
    app.router.add_post("/api/connections/{id}/tags", add_tag)
    app.router.add_delete("/api/connections/{id}/tags/{tag_id}", delete_tag)
    app.router.add_post("/api/connections/{id}/tags/import", import_tags_csv)
    app.router.add_get("/api/connections/{id}/tags/export", export_tags_csv)
    app.router.add_get("/api/connections/{id}/browse", browse_connection)


# Import CONNECTOR_REGISTRY at module level for validate/test endpoints
from agent.connectors.registry import CONNECTOR_REGISTRY
