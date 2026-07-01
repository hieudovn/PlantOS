"""Authentication middleware — JWT + API Key."""

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.security import decode_access_token
from app.core.config import settings

PUBLIC_PATHS = [
    "/health",
    "/api/v1/auth/login",
    "/docs",
    "/openapi.json",
    "/api/v1/edge/sync/manifest",   # Edge Agent metadata bootstrap
]


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # Skip public paths
        if any(path.startswith(p) for p in PUBLIC_PATHS):
            return await call_next(request)

        # Bypass auth in debug/dev mode (tests run without auth)
        if settings.DEBUG:
            return await call_next(request)

        # API Key auth (for Edge Agent, external clients)
        api_key = request.headers.get("X-API-Key")
        if api_key and settings.API_KEYS:
            valid_keys = [k.strip() for k in settings.API_KEYS.split(",") if k.strip()]
            if api_key in valid_keys:
                return await call_next(request)

        # JWT auth (for UI users)
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
            payload = decode_access_token(token)
            if payload:
                request.state.user = payload
                return await call_next(request)

        return JSONResponse(
            status_code=401,
            content={"detail": "Invalid or missing authentication"},
        )
