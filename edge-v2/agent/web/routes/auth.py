"""Auth API routes — login, logout, setup, change-password, me."""

import logging

from aiohttp import web

logger = logging.getLogger(__name__)

COOKIE_NAME = "plantos_session"
COOKIE_PATH = "/"
COOKIE_MAX_AGE = 86400  # 24 hours


def _set_session_cookie(response: web.Response, cookie_value: str, csrf_token: str = ""):
    """Set HttpOnly session cookie + readable CSRF cookie."""
    response.set_cookie(
        COOKIE_NAME,
        cookie_value,
        path=COOKIE_PATH,
        max_age=COOKIE_MAX_AGE,
        httponly=True,
        samesite="Lax",
    )
    # CSRF token — non-HttpOnly so JS can read it
    if csrf_token:
        response.set_cookie(
            "plantos_csrf",
            csrf_token,
            path=COOKIE_PATH,
            max_age=COOKIE_MAX_AGE,
            httponly=False,
            samesite="Lax",
        )


def _clear_session_cookie(response: web.Response):
    """Clear the session cookie."""
    response.del_cookie(COOKIE_NAME, path=COOKIE_PATH)


def register_auth_routes(app: web.Application, auth):
    """Register auth-related API routes."""

    # ---- POST /api/auth/setup — first-run admin password creation -----------
    async def setup(request: web.Request) -> web.Response:
        if not auth.is_first_run():
            return web.json_response(
                {"error": "Admin already configured"}, status=400
            )
        try:
            body = await request.json()
        except Exception:
            return web.json_response({"error": "Invalid JSON"}, status=400)

        password = body.get("password", "")
        if len(password) < 6:
            return web.json_response(
                {"error": "Password must be at least 6 characters"}, status=400
            )

        auth.create_admin(password)
        return web.json_response({"status": "ok", "message": "Admin password created"})

    # ---- POST /api/auth/login -----------------------------------------------
    async def login(request: web.Request) -> web.Response:
        try:
            body = await request.json()
        except Exception:
            return web.json_response({"error": "Invalid JSON"}, status=400)

        username = body.get("username", "")
        password = body.get("password", "")

        if not auth.verify_password(username, password):
            return web.json_response(
                {"error": "Invalid credentials"}, status=401
            )

        user = auth.user_store.get_user(username)
        role = user.role if user else "operator"
        cookie_value, session = auth.create_session(username, role=role)
        resp = web.json_response({
            "status": "ok",
            "role": session.role,
            "display_name": user.display_name if user else "Administrator",
            "redirect": "/dashboard.html",
        })
        _set_session_cookie(resp, cookie_value, session.csrf_token)
        return resp

    # ---- POST /api/auth/logout ----------------------------------------------
    async def logout(request: web.Request) -> web.Response:
        cookie = request.cookies.get(COOKIE_NAME, "")
        auth.destroy_session(cookie)
        resp = web.json_response({"status": "ok"})
        _clear_session_cookie(resp)
        return resp

    # ---- POST /api/auth/change-password -------------------------------------
    async def change_password(request: web.Request) -> web.Response:
        try:
            body = await request.json()
        except Exception:
            return web.json_response({"error": "Invalid JSON"}, status=400)

        username = body.get("username", "")
        old_pw = body.get("old_password", "")
        new_pw = body.get("new_password", "")

        if not username:
            # Fallback to session user
            user_data = request.get("user")
            if user_data:
                username = user_data.get("username", "")

        if not username:
            return web.json_response({"error": "Username required"}, status=400)

        if len(new_pw) < 6:
            return web.json_response(
                {"error": "New password must be at least 6 characters"}, status=400
            )

        if auth.change_password(username, old_pw, new_pw):
            # Invalidate current session
            cookie = request.cookies.get(COOKIE_NAME, "")
            auth.destroy_session(cookie)
            resp = web.json_response({
                "status": "ok",
                "message": "Password changed — please log in again",
            })
            _clear_session_cookie(resp)
            return resp

        return web.json_response({"error": "Invalid current password"}, status=401)

    # ---- GET /api/auth/me ---------------------------------------------------
    async def me(request: web.Request) -> web.Response:
        user = request.get("user")
        if not user:
            return web.json_response({"error": "Not authenticated"}, status=401)

        username = user.get("username", "")
        user_info = auth.user_store.get_user(username)
        return web.json_response({
            "username": user["username"],
            "role": user["role"],
            "display_name": user_info.display_name if user_info else user["username"],
        })

    # ---- GET /api/auth/users — list local users (admin only) ----------------
    async def list_users(request: web.Request) -> web.Response:
        """List all locally cached users (admin only)."""
        users = auth.user_store.list_users()
        return web.json_response([
            {
                "username": u.username,
                "display_name": u.display_name,
                "role": u.role,
                "is_active": u.is_active,
                "synced_at": u.synced_at.isoformat() if u.synced_at else None,
            }
            for u in users
        ])

    # ---- POST /api/auth/users/sync — receive users from Center -------------
    async def sync_users(request: web.Request) -> web.Response:
        """Receive user list from Center and update local cache."""
        try:
            body = await request.json()
        except Exception:
            return web.json_response({"error": "Invalid JSON"}, status=400)

        center_users = body.get("users", [])
        if not center_users:
            return web.json_response({"error": "No users provided"}, status=400)

        auth.user_store.sync_from_center(center_users)
        return web.json_response({
            "status": "ok",
            "count": len(center_users),
            "synced_at": body.get("synced_at", ""),
        })

    # Register routes
    app.router.add_post("/api/auth/setup", setup)
    app.router.add_post("/api/auth/login", login)
    app.router.add_post("/api/auth/logout", logout)
    app.router.add_post("/api/auth/change-password", change_password)
    app.router.add_get("/api/auth/me", me)
    app.router.add_get("/api/auth/users", list_users)
    app.router.add_post("/api/auth/users/sync", sync_users)
