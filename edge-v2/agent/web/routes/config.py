"""Config API routes — sanitized config export."""

import logging

from aiohttp import web

logger = logging.getLogger(__name__)

# Keys whose values must be redacted in API output
SECRET_KEYS = {"api_key", "password", "secret", "hash", "token", "admin_hash",
               "session_secret", "session_secret_ref", "password_secret_ref"}


def _sanitize(obj):
    """Recursively sanitize a config dict, masking secret values."""
    if isinstance(obj, dict):
        return {k: _sanitize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_sanitize(v) for v in obj]
    return obj


def _redact_secrets(obj, parent_key: str = ""):
    """Recursively redact secret values, replacing with ***REDACTED***."""
    if isinstance(obj, dict):
        return {
            k: "***REDACTED***"
            if any(secret in k.lower() for secret in SECRET_KEYS)
            else _redact_secrets(v, k)
            for k, v in obj.items()
        }
    if isinstance(obj, list):
        return [_redact_secrets(v, parent_key) for v in obj]
    return obj


def register_config_routes(app: web.Application, config):
    """Register config-related API routes."""

    # ---- GET /api/config — sanitized config (no secrets) --------------------
    async def get_config(request: web.Request) -> web.Response:
        raw = config.get("__all__", config._data)
        sanitized = _redact_secrets(raw)
        return web.json_response(sanitized)

    # ---- POST /api/config/export — download sanitized config ----------------
    async def export_config(request: web.Request) -> web.Response:
        raw = config.get("__all__", config._data)
        sanitized = _redact_secrets(raw)
        return web.json_response(sanitized)

    app.router.add_get("/api/config", get_config)
    app.router.add_post("/api/config/export", export_config)
