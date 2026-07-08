"""aiohttp middleware — session auth, CSRF protection.

- Checks session cookie on all /api/* routes
- Exempts: /api/auth/login, /api/auth/setup, /api/status
- Returns 401 JSON if invalid/missing session
- Returns 403 JSON if CSRF token missing/invalid on POST/PUT/DELETE
- Injects request['user'] with {username, role} for downstream handlers
"""

import json
import logging
from typing import Callable

from aiohttp import web

from agent.auth.auth import LocalAuthManager

logger = logging.getLogger(__name__)

# Routes that do NOT require authentication
PUBLIC_ROUTES = {
    "/api/auth/login",
    "/api/auth/setup",
    "/api/status",
}

# HTTP methods that require CSRF protection
CSRF_METHODS = {"POST", "PUT", "DELETE", "PATCH"}


def auth_middleware_factory(auth: LocalAuthManager) -> Callable:
    """Create an aiohttp middleware bound to the given auth manager."""

    @web.middleware
    async def auth_middleware(request: web.Request, handler: Callable) -> web.Response:
        path = request.path

        # Always allow public routes
        if path in PUBLIC_ROUTES:
            return await handler(request)

        # Protect all /api/* routes
        if path.startswith("/api/"):
            session_cookie = request.cookies.get("plantos_session", "").strip('"')
            session = auth.validate_session(session_cookie)

            if not session:
                return web.json_response(
                    {"error": "Unauthorized", "detail": "Missing or invalid session"},
                    status=401,
                )

            # Inject user info into request
            request["user"] = {
                "username": session.username,
                "role": session.role,
            }

            # CSRF check for state-changing methods
            if request.method in CSRF_METHODS:
                csrf_header = request.headers.get("X-CSRF-Token", "")
                if not auth.validate_csrf(session_cookie, csrf_header):
                    return web.json_response(
                        {"error": "Forbidden", "detail": "Missing or invalid CSRF token"},
                        status=403,
                    )

            return await handler(request)

        # Non-API routes (static files, login page, etc.) — allow
        return await handler(request)

    return auth_middleware
