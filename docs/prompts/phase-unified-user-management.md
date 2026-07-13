# Task: Fix Users Page + Unified Edge User Management

> **Role:** Coder-Executioner (V4 Flash)
> **Reviewer:** PM-Designer (V4 Pro)
> **Scope:** Fix Center Users page (P0) + Edge v2 multi-user with Center sync (P1)
> **Constraint:** Do NOT modify docs/reports/runbooks. Do NOT break existing login.

---

## Part A: Fix Center Users Page (P0 — 1 line)

### A.1 Problem

`backend/app/modules/users/router.py` has full CRUD but is never registered. `/api/v1/users` returns 404.

### A.2 Fix

**File:** `backend/app/api/v1.py`

Add 2 lines (import + include_router):

```python
# ADD this import (after the other imports):
from app.modules.users.router import router as users_router

# ADD this include_router (before the closing line):
router.include_router(users_router, tags=["Users"])
```

Full file after fix:

```python
"""API v1 router — aggregates all module routers."""

from fastapi import APIRouter

from app.modules.assets.router import router as assets_router
from app.modules.signals.router import router as signals_router
from app.modules.measurements.router import router as measurements_router
from app.modules.edge_nodes.router import router as edge_nodes_router
from app.modules.alarms.router import router as alarms_router
from app.modules.events.router import router as events_router
from app.modules.system.router import router as system_router
from app.modules.contracts.router import router as contracts_router
from app.modules.asset_templates.router import router as templates_router
from app.modules.formulas.router import router as formulas_router
from app.modules.process_view.router import router as process_view_router
from app.modules.users.router import router as users_router

router = APIRouter(prefix="/api/v1")
router.include_router(assets_router, tags=["Assets"])
router.include_router(signals_router, tags=["Signals"])
router.include_router(measurements_router, tags=["Measurements"])
router.include_router(edge_nodes_router, tags=["Edge Nodes"])
router.include_router(alarms_router, tags=["Alarms"])
router.include_router(events_router, tags=["Events"])
router.include_router(system_router, tags=["System"])
router.include_router(contracts_router, tags=["Contracts"])
router.include_router(templates_router, tags=["Asset Templates"])
router.include_router(formulas_router, tags=["Formulas"])
router.include_router(process_view_router, tags=["Process View"])
router.include_router(users_router, tags=["Users"])
```

### A.3 Deploy & Verify

```bash
# 1. Copy updated file to VPS
scp backend/app/api/v1.py plantos@103.97.132.249:/opt/plantos/backend/app/api/v1.py

# 2. Copy into Docker container
ssh plantos@103.97.132.249 'docker cp /opt/plantos/backend/app/api/v1.py plantos-backend:/app/app/api/v1.py'

# 3. Restart backend
ssh plantos@103.97.132.249 'docker restart plantos-backend'
sleep 5

# 4. Test
ssh plantos@103.97.132.249 '
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"admin\",\"password\":\"PlantOS@2026!\"}" | \
  python3 -c "import sys,json; print(json.load(sys.stdin).get(\"access_token\",\"\"))")
echo "Token: ${TOKEN:0:20}..."
curl -s http://localhost:8000/api/v1/users \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
'
```

**Expected:** JSON array with 3 users (admin, engineer, operator).

---

## Part B: Edge v2 Multi-User + Center Sync (P1)

### B.1 Current State

Edge v2 `LocalAuthManager.verify_password()`:
```python
def verify_password(self, username: str, password: str) -> bool:
    if username != "admin":
        return False  # ← ONLY admin supported
    ...
```

Edge stores single `admin_hash` in config YAML. No multi-user support.

### B.2 New Architecture

```
Center PostgreSQL           Edge v2 Local
┌──────────────┐          ┌─────────────────────┐
│ users table  │ ─sync──→ │ LocalUserStore       │
│ (PG)         │          │ (YAML or SQLite)     │
│              │          │                      │
│ edge_user_   │          │ GET /api/auth/users   │
│ assignments  │          │ POST /api/auth/users/ │
│ (PG)         │          │      sync             │
└──────────────┘          └─────────────────────┘
```

### B.3 Files to Create

#### B.3.1 `edge-v2/agent/auth/local_user_store.py` (NEW)

```python
"""LocalUserStore — local cache of users synced from Center.

Stores user credentials locally so Edge can authenticate offline.
Format (YAML in config file):
  auth:
    users:
      admin:
        password_hash: $2b$12$...
        display_name: Administrator
        role: admin
        synced_at: "2026-07-13T00:00:00Z"
      engineer:
        password_hash: $2b$12$...
        display_name: Engineer
        role: engineer
        synced_at: "2026-07-13T00:00:00Z"
"""

from __future__ import annotations
import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


class UserInfo:
    """Represents a cached user."""
    def __init__(self, username: str, password_hash: str, display_name: str,
                 role: str, is_active: bool = True,
                 synced_at: datetime | None = None):
        self.username = username
        self.password_hash = password_hash
        self.display_name = display_name
        self.role = role
        self.is_active = is_active
        self.synced_at = synced_at or datetime.now(timezone.utc)

    def to_dict(self) -> dict:
        return {
            "password_hash": self.password_hash,
            "display_name": self.display_name,
            "role": self.role,
            "is_active": self.is_active,
            "synced_at": self.synced_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, username: str, data: dict) -> "UserInfo":
        synced = data.get("synced_at")
        if synced:
            synced = datetime.fromisoformat(synced)
        return cls(
            username=username,
            password_hash=data["password_hash"],
            display_name=data.get("display_name", username),
            role=data.get("role", "operator"),
            is_active=data.get("is_active", True),
            synced_at=synced,
        )


class LocalUserStore:
    """Local cache of authorized users, synced from Center."""

    def __init__(self, config):
        self.config = config
        self._users: dict[str, UserInfo] = {}
        self._load()

    def _load(self):
        """Load users from config."""
        users_dict = self.config.get("auth", {}).get("users", {})
        self._users = {}
        for username, data in users_dict.items():
            try:
                self._users[username] = UserInfo.from_dict(username, data)
            except Exception as e:
                logger.warning("Failed to load user %s: %s", username, e)

    def _save(self):
        """Save users to config."""
        data = {}
        for username, user in self._users.items():
            data[username] = user.to_dict()
        self.config._data.setdefault("auth", {})["users"] = data
        self.config._save()
        logger.info("Saved %d users to local config", len(self._users))

    # ---- Migration: convert legacy admin_hash to users dict ----

    def migrate_legacy_admin(self, password_verifier) -> bool:
        """If legacy admin_hash exists, migrate to users dict. Returns True if migrated."""
        legacy_hash = self.config.get("auth", {}).get("admin_hash")
        if not legacy_hash:
            return False
        if self._users:
            return False  # already migrated

        self._users["admin"] = UserInfo(
            username="admin",
            password_hash=legacy_hash,
            display_name="Administrator",
            role="admin",
        )
        # Remove legacy key
        if "admin_hash" in self.config._data.get("auth", {}):
            del self.config._data["auth"]["admin_hash"]
        self._save()
        logger.info("Migrated legacy admin_hash to users dict")
        return True

    # ---- CRUD ----

    def get_user(self, username: str) -> UserInfo | None:
        return self._users.get(username)

    def list_users(self) -> list[UserInfo]:
        return list(self._users.values())

    def upsert_user(self, user: UserInfo):
        self._users[user.username] = user
        self._save()

    def delete_user(self, username: str) -> bool:
        if username not in self._users:
            return False
        del self._users[username]
        self._save()
        return True

    # ---- Sync ----

    def sync_from_center(self, center_users: list[dict]):
        """Replace local user list with Center data. Called on push or pull."""
        now = datetime.now(timezone.utc)
        new_users: dict[str, UserInfo] = {}
        for u in center_users:
            username = u["username"]
            new_users[username] = UserInfo(
                username=username,
                password_hash=u["password_hash"],
                display_name=u.get("display_name", username),
                role=u.get("role", "operator"),
                is_active=u.get("is_active", True),
                synced_at=now,
            )
        self._users = new_users
        self._save()
        logger.info("Synced %d users from Center", len(self._users))

    def get_sync_timestamp(self) -> str | None:
        """Get timestamp of last sync for incremental pull."""
        if not self._users:
            return None
        latest = max((u.synced_at for u in self._users.values()),
                     default=None)
        return latest.isoformat() if latest else None

    def __len__(self):
        return len(self._users)
```

#### B.3.2 `backend/app/modules/edge_users/router.py` (NEW)

```python
"""Edge Users API — assign users to edge nodes and push sync."""

import logging
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text

from app.db import get_session
from app.middleware.auth import require_admin

logger = logging.getLogger(__name__)
router = APIRouter()


# ---- Schemas ----

class EdgeUserAssignRequest(BaseModel):
    user_id: str

class EdgeUserOut(BaseModel):
    user_id: str
    username: str
    display_name: str
    role: str
    is_active: bool

class EdgeUserSyncPayload(BaseModel):
    """Payload sent to Edge for user sync."""
    users: list[dict]  # [{username, password_hash, display_name, role, is_active}]
    synced_at: str


# ---- Endpoints ----

@router.get("/edges/{edge_node_id}/users", response_model=list[EdgeUserOut],
            dependencies=[Depends(require_admin)])
def list_edge_users(edge_node_id: str):
    """List users assigned to an edge node (admin only)."""
    with get_session() as session:
        rows = session.execute(
            text("""
                SELECT u.id, u.username, u.display_name, u.role, u.is_active
                FROM users u
                JOIN edge_user_assignments eua ON u.id = eua.user_id
                WHERE eua.edge_node_id = :eid
                ORDER BY u.username
            """),
            {"eid": edge_node_id},
        ).fetchall()
        return [
            EdgeUserOut(
                user_id=str(r[0]),
                username=r[1],
                display_name=r[2],
                role=r[3],
                is_active=r[4],
            )
            for r in rows
        ]


@router.post("/edges/{edge_node_id}/users", status_code=201,
             dependencies=[Depends(require_admin)])
def assign_user_to_edge(edge_node_id: str, body: EdgeUserAssignRequest):
    """Assign a user to an edge node (admin only)."""
    with get_session() as session:
        # Verify user exists
        user = session.execute(
            text("SELECT id, username FROM users WHERE id = :uid"),
            {"uid": body.user_id},
        ).fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Check if already assigned
        existing = session.execute(
            text("SELECT id FROM edge_user_assignments WHERE edge_node_id = :eid AND user_id = :uid"),
            {"eid": edge_node_id, "uid": body.user_id},
        ).fetchone()
        if existing:
            raise HTTPException(status_code=409, detail="User already assigned to this edge")

        session.execute(
            text("INSERT INTO edge_user_assignments (id, edge_node_id, user_id) VALUES (:id, :eid, :uid)"),
            {"id": str(uuid4()), "eid": edge_node_id, "uid": body.user_id},
        )
        session.commit()
    return {"status": "ok", "message": f"User {user[1]} assigned to edge {edge_node_id}"}


@router.delete("/edges/{edge_node_id}/users/{user_id}", status_code=204,
               dependencies=[Depends(require_admin)])
def remove_user_from_edge(edge_node_id: str, user_id: str):
    """Remove a user assignment from an edge node (admin only)."""
    with get_session() as session:
        result = session.execute(
            text("DELETE FROM edge_user_assignments WHERE edge_node_id = :eid AND user_id = :uid"),
            {"eid": edge_node_id, "uid": user_id},
        )
        session.commit()
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Assignment not found")


@router.post("/edges/{edge_node_id}/users/sync",
             dependencies=[Depends(require_admin)])
def push_users_to_edge(edge_node_id: str):
    """Push assigned users to an edge node. Returns sync payload."""
    with get_session() as session:
        rows = session.execute(
            text("""
                SELECT u.username, u.password_hash, u.display_name, u.role, u.is_active
                FROM users u
                JOIN edge_user_assignments eua ON u.id = eua.user_id
                WHERE eua.edge_node_id = :eid AND u.is_active = TRUE
            """),
            {"eid": edge_node_id},
        ).fetchall()

        if not rows:
            return {"users": [], "synced_at": datetime.now(timezone.utc).isoformat(),
                    "message": "No users assigned to this edge"}

        users = [
            {
                "username": r[0],
                "password_hash": r[1],
                "display_name": r[2],
                "role": r[3],
                "is_active": r[4],
            }
            for r in rows
        ]
        return {
            "users": users,
            "synced_at": datetime.now(timezone.utc).isoformat(),
        }


@router.get("/edges/{edge_node_id}/users/export",
            dependencies=[Depends(require_admin)])
def export_edge_users(edge_node_id: str):
    """Export user list for edge pull (same as push but GET for edge-initiated sync)."""
    with get_session() as session:
        rows = session.execute(
            text("""
                SELECT u.username, u.password_hash, u.display_name, u.role, u.is_active
                FROM users u
                JOIN edge_user_assignments eua ON u.id = eua.user_id
                WHERE eua.edge_node_id = :eid AND u.is_active = TRUE
            """),
            {"eid": edge_node_id},
        ).fetchall()

        users = [
            {
                "username": r[0],
                "password_hash": r[1],
                "display_name": r[2],
                "role": r[3],
                "is_active": r[4],
            }
            for r in rows
        ]
        return {
            "users": users,
            "synced_at": datetime.now(timezone.utc).isoformat(),
        }
```

#### B.3.3 Migration file (NEW)

**File:** `backend/migrations/versions/005_edge_user_assignments.py`

```python
"""edge_user_assignments

Revision ID: 005
Create Date: 2026-07-13
"""
from alembic import op
import sqlalchemy as sa

revision = "005"
down_revision = "004"


def upgrade():
    op.create_table(
        "edge_user_assignments",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("edge_node_id", sa.String(128), nullable=False),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index("ix_eua_edge_node", "edge_user_assignments", ["edge_node_id"])
    op.create_index("ix_eua_user", "edge_user_assignments", ["user_id"])
    op.create_unique_constraint("uq_eua_edge_user", "edge_user_assignments",
                                ["edge_node_id", "user_id"])

    # Seed: assign all 3 default users to EDGEV2-PC-01
    op.execute("""
        INSERT INTO edge_user_assignments (id, edge_node_id, user_id)
        SELECT gen_random_uuid(), 'EDGEV2-PC-01', id FROM users
    """)


def downgrade():
    op.drop_table("edge_user_assignments")
```

### B.4 Files to Modify

#### B.4.1 `edge-v2/agent/auth/auth.py` — Multi-user support

**Change `verify_password`:**

```python
# REPLACE existing verify_password with:

def verify_password(self, username: str, password: str) -> bool:
    """Verify username/password against local user store."""
    user = self._user_store.get_user(username)
    if not user:
        return False
    if not user.is_active:
        return False
    return _check_password(password, user.password_hash)
```

**Change `change_password`:**

```python
# REPLACE existing change_password with:

def change_password(self, username: str, old_password: str, new_password: str) -> bool:
    """Change password for any local user. Requires old password verification."""
    if not self.verify_password(username, old_password):
        return False
    user = self._user_store.get_user(username)
    if not user:
        return False
    user.password_hash = _hash_password(new_password)
    self._user_store.upsert_user(user)
    self._sessions.clear()
    logger.info("Password changed for %s — all sessions invalidated", username)
    return True
```

**Change `__init__`:**

```python
# ADD to __init__ (after self._sessions = {}):
from agent.auth.local_user_store import LocalUserStore
self._user_store = LocalUserStore(config)
self._user_store.migrate_legacy_admin(lambda pw, h: _check_password(pw, h))
# NOTE: the lambda is unused by migrate_legacy_admin but kept for clarity
self._user_store.migrate_legacy_admin()
```

**Change `has_admin`:**

```python
def has_admin(self) -> bool:
    """Check if any admin user exists in local store."""
    return any(u.role == "admin" for u in self._user_store.list_users())

# Also update is_first_run to use has_admin
```

**Change `create_admin`:**

```python
def create_admin(self, password: str) -> bool:
    """Set the admin password (first-run). Returns False if already exists."""
    if self.has_admin():
        return False
    self._user_store.upsert_user(UserInfo(
        username="admin",
        password_hash=_hash_password(password),
        display_name="Administrator",
        role="admin",
    ))
    logger.info("Admin user created")
    return True
```

**Add import at top:**
```python
from agent.auth.local_user_store import LocalUserStore, UserInfo
```

**Add property:**
```python
@property
def user_store(self) -> "LocalUserStore":
    return self._user_store
```

#### B.4.2 `edge-v2/agent/web/routes/auth.py` — Multi-user routes

**Modify login to return user's actual role:**

```python
# In login handler, replace:
#   cookie_value, session = auth.create_session(username, role="admin")
# WITH:
user = auth.user_store.get_user(username)
cookie_value, session = auth.create_session(username, role=user.role if user else "operator")
```

**Add new routes in `register_auth_routes`:**

```python
# ---- GET /api/auth/users — list local users (admin only) ----
async def list_users(request: web.Request) -> web.Response:
    """List all locally cached users."""
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

# ---- POST /api/auth/users/sync — receive users from Center ----
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

# Register routes:
app.router.add_get("/api/auth/users", list_users)
app.router.add_post("/api/auth/users/sync", sync_users)
```

**Also update login response to include display_name:**
```python
# In login handler response, add display_name:
user = auth.user_store.get_user(username)
resp = web.json_response({
    "status": "ok",
    "role": user.role if user else "admin",
    "display_name": user.display_name if user else "Administrator",
    "redirect": "/dashboard.html",
})
```

#### B.4.3 `backend/app/api/v1.py` — Register edge_users router

```python
# ADD import:
from app.modules.edge_users.router import router as edge_users_router

# ADD include_router (after users_router):
router.include_router(edge_users_router, tags=["Edge Users"])
```

### B.5 Edge v2 Main — Sync on Startup

**File:** `edge-v2/agent/main.py`

Add sync logic after JWT login in the startup sequence:

```python
async def _sync_users_from_center(self):
    """Pull user list from Center on startup."""
    try:
        import httpx
        async with httpx.AsyncClient(timeout=10) as client:
            # Use JWT token for auth
            headers = {}
            if hasattr(self, '_jwt_token') and self._jwt_token:
                headers["Authorization"] = f"Bearer {self._jwt_token}"

            edge_id = self.config.get("edge_node_id", "EDGEV2-PC-01")
            resp = await client.get(
                f"{self.config.center_url}/api/v1/edges/{edge_id}/users/export",
                headers=headers,
            )
            if resp.status_code == 200:
                data = resp.json()
                users = data.get("users", [])
                if users:
                    self.auth.user_store.sync_from_center(users)
                    logger.info("Synced %d users from Center on startup", len(users))
            else:
                logger.warning("Center user sync returned %d", resp.status_code)
    except Exception as e:
        logger.warning("Failed to sync users from Center: %s", e)
```

Call this after `_jwt_login()` in the startup sequence (around line 178 in current main.py, after `await self._jwt_login()`).

---

## Part C: Deploy & Test

### C.1 Deploy Backend

```bash
# 1. Run migration on VPS
ssh plantos@103.97.132.249 'cd /opt/plantos && docker exec plantos-backend alembic upgrade head'

# 2. Copy files
scp backend/app/api/v1.py plantos@103.97.132.249:/opt/plantos/backend/app/api/v1.py
scp backend/app/modules/edge_users/router.py plantos@103.97.132.249:/opt/plantos/backend/app/modules/edge_users/router.py
scp backend/migrations/versions/005_edge_user_assignments.py plantos@103.97.132.249:/opt/plantos/backend/migrations/versions/005_edge_user_assignments.py

# 3. Copy into Docker
ssh plantos@103.97.132.249 '
  docker cp /opt/plantos/backend/app/api/v1.py plantos-backend:/app/app/api/v1.py
  docker cp /opt/plantos/backend/app/modules/edge_users/router.py plantos-backend:/app/app/modules/edge_users/router.py
  docker cp /opt/plantos/backend/migrations/versions/005_edge_user_assignments.py plantos-backend:/app/migrations/versions/005_edge_user_assignments.py
'

# 4. Restart
ssh plantos@103.97.132.249 'docker restart plantos-backend'
sleep 5
```

### C.2 Deploy Edge v2

```bash
# Build new Docker image locally, then deploy to VPS
# (or copy files and hot-reload if supported)

# Option 1: Rebuild image
cd edge-v2
docker build -t plantos-edge-v2:unified-users .
docker save plantos-edge-v2:unified-users -o plantos-edge-v2-unified.tar
scp plantos-edge-v2-unified.tar plantos@103.97.132.249:/tmp/
ssh plantos@103.97.132.249 '
  docker load -i /tmp/plantos-edge-v2-unified.tar
  docker stop plantos-edge-v2
  docker rm plantos-edge-v2
  # Re-run with same flags as original
  docker run -d --name plantos-edge-v2 --network host \
    -v /opt/plantos/edge-v2/data:/app/data \
    plantos-edge-v2:unified-users
'
```

### C.3 Test API

```bash
# Test 1: Center Users API
TOKEN=$(curl -s -X POST http://103.97.132.249:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"PlantOS@2026!"}' | \
  python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token',''))")

# List users
curl -s http://103.97.132.249:8000/api/v1/users \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

# List edge users
curl -s http://103.97.132.249:8000/api/v1/edges/EDGEV2-PC-01/users \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

# Push sync to edge
curl -s -X POST http://103.97.132.249:8000/api/v1/edges/EDGEV2-PC-01/users/sync \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

# Test 2: Edge v2 local users
curl -s http://103.97.132.249:8011/api/auth/users \
  -H "Cookie: plantos_session=<session_from_login>" | python3 -m json.tool

# Test 3: Login with engineer account on Edge v2
curl -s -X POST http://103.97.132.249:8011/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"engineer","password":"PlantOS@2026!"}'
```

---

## Part D: Rollback

### Backend

```bash
# Revert v1.py from git
git checkout backend/app/api/v1.py
# Re-deploy to VPS + Docker
```

### Edge v2

```bash
# Revert to previous image
docker stop plantos-edge-v2
docker rm plantos-edge-v2
docker run -d --name plantos-edge-v2 --network host \
  -v /opt/plantos/edge-v2/data:/app/data \
  plantos-edge-v2:patched
```

---

## Part E: Expected Results

| Test | Expected |
|---|---|
| `GET /api/v1/users` | 200, 3 users (admin, engineer, operator) |
| `GET /api/v1/edges/EDGEV2-PC-01/users` | 200, 3 assigned users |
| `POST /api/v1/edges/EDGEV2-PC-01/users/sync` | 200, users array |
| Edge v2 `GET /api/auth/users` | 200, local user list |
| Edge v2 login as `engineer` | 200, role=engineer |
| Edge v2 login as `admin` | 200, role=admin |
| Edge v2 login as `operator` | 200, role=operator |
| Center Users page (UI) | Loads with user table |
