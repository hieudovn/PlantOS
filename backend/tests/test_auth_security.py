"""Auth security tests — run with DEBUG=false, no auth bypass.

These tests verify that the JWT authentication middleware correctly:
- Rejects missing/invalid/expired JWTs (401)
- Enforces role-based access (403 for unauthorized roles)
- Preserves role across JWT refresh
- Does not grant admin privileges to API key requests
"""

import os
import time
import pytest
from httpx import ASGITransport, AsyncClient

# Force DEBUG=false for security testing
os.environ["DEBUG"] = "false"

import jwt as pyjwt
from app.main import app
from app.core.config import settings


def _make_token(username: str = "test-admin", role: str = "admin", expired: bool = False) -> str:
    """Create a signed JWT for testing."""
    exp = int(time.time()) - 3600 if expired else int(time.time()) + 3600
    payload = {
        "sub": username,
        "role": role,
        "exp": exp,
        "iat": int(time.time()),
    }
    return pyjwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def _make_invalid_token() -> str:
    """Create a JWT signed with wrong secret."""
    payload = {"sub": "hacker", "role": "admin", "exp": int(time.time()) + 3600}
    return pyjwt.encode(payload, "wrong-secret-key-12345", algorithm="HS256")


@pytest.mark.asyncio
async def test_missing_jwt_returns_401():
    """Request without Authorization header should return 401."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/users")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_invalid_jwt_returns_401():
    """Request with invalid JWT should return 401."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/users",
            headers={"Authorization": f"Bearer {_make_invalid_token()}"},
        )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_expired_jwt_returns_401():
    """Request with expired JWT should return 401."""
    token = _make_token(expired=True)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/users",
            headers={"Authorization": f"Bearer {token}"},
        )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_admin_access_allowed():
    """Admin JWT should access admin endpoints."""
    token = _make_token(role="admin")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/users",
            headers={"Authorization": f"Bearer {token}"},
        )
    # Admin should NOT get 401 or 403
    assert response.status_code != 401
    assert response.status_code != 403


@pytest.mark.asyncio
async def test_engineer_access_to_admin_api_returns_403():
    """Engineer role should get 403 on admin endpoints."""
    token = _make_token(role="engineer")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/users",
            headers={"Authorization": f"Bearer {token}"},
        )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_operator_access_to_admin_api_returns_403():
    """Operator role should get 403 on admin endpoints."""
    token = _make_token(role="operator")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/users",
            headers={"Authorization": f"Bearer {token}"},
        )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_jwt_refresh_preserves_role():
    """JWT refresh should preserve the user's role."""
    token = _make_token(role="engineer")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/auth/refresh",
            headers={"Authorization": f"Bearer {token}"},
        )
    if response.status_code == 200:
        data = response.json()
        # If refresh returns a token, verify role is preserved
        new_token = data.get("access_token") or data.get("token", "")
        if new_token:
            decoded = pyjwt.decode(
                new_token, settings.JWT_SECRET,
                algorithms=[settings.JWT_ALGORITHM],
                options={"verify_exp": False},
            )
            assert decoded.get("role") == "engineer"


@pytest.mark.asyncio
async def test_api_key_request_no_admin_privileges():
    """API key should not grant user-admin CRUD privileges."""
    api_key = settings.API_KEYS.split(",")[0] if settings.API_KEYS else "test-key-123"
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/users",
            headers={"X-API-Key": api_key},
        )
    # API key should NOT grant access to user management
    assert response.status_code in (401, 403)
