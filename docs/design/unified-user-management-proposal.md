# Unified User Management — Proposal & Design

> **Date:** 2026-07-13
> **Author:** PM-Designer (DeepSeek V4 Pro)
> **Status:** DRAFT — pending review

---

## 1. Current State Assessment

### 1.1 Center Auth (what EXISTS)

| Component | Status |
|---|---|
| `backend/app/modules/auth/router.py` | ✅ JWT login, bcrypt password verify |
| `backend/app/modules/users/router.py` | ✅ Full CRUD coded (list, get, create, update, delete) |
| `backend/app/api/v1.py` | 🔴 Users router **NOT REGISTERED** → `/api/v1/users` = 404 |
| `backend/migrations/versions/004_users_table.py` | ✅ Creates `users` table + seeds 3 users |
| `frontend/src/features/users/UserManagementPage.tsx` | ✅ Full UI: table, modal create/edit, delete |
| `frontend/src/components/layout/Sidebar.tsx` | ✅ "Users" menu item at `/users` |

**Root cause:** The users router (`backend/app/modules/users/router.py`) is fully coded but never imported into `backend/app/api/v1.py`. One-line fix.

### 1.2 Center User Model (PostgreSQL)

```sql
users (
    id UUID PRIMARY KEY,
    username VARCHAR(64) UNIQUE,
    password_hash VARCHAR(256),   -- bcrypt
    display_name VARCHAR(128),
    role VARCHAR(20),             -- admin | engineer | operator
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
)
```

Seeded users: `admin`, `engineer`, `operator` (password: `PlantOS@2026!`)

### 1.3 Edge v2 Auth (what EXISTS)

| Component | Status |
|---|---|
| `edge-v2/agent/auth/auth.py` | ✅ bcrypt hash, signed session cookies, CSRF |
| `edge-v2/agent/auth/middleware.py` | ✅ Protects `/api/*` routes |
| `edge-v2/agent/web/routes/auth.py` | ✅ login, logout, setup, change-password, me |
| Multi-user support | 🔴 **Only `admin` user**, hardcoded |
| User storage | YAML config file (`admin_hash` key) |
| PostgreSQL integration | 🔴 None — fully local |

### 1.4 Gap Summary

| Gap | Severity |
|---|---|
| Users API not registered → UI broken | 🔴 P0 — fix immediately |
| Edge v2 only supports 1 user (admin) | 🟡 P1 — blocks multi-user Edge access |
| No unified user management across Center ↔ Edge | 🟡 P1 — users managed separately |
| Edge user list not accessible from Center | 🟡 P1 — no visibility from Center |

---

## 2. Proposed Architecture: Center-Managed Users + Edge Local Caching

### 2.1 Design Principles

1. **Center is source of truth** for all users in the system
2. **Edge operates autonomously** — local credential cache for offline
3. **Center UI manages everything** — admin doesn't need to SSH into Edge
4. **Push + Pull model** — Center pushes to Edge on change; Edge pulls on startup
5. **No direct DB access** from Edge (respects PlantOS constitution)

### 2.2 Architecture Diagram

```
┌─────────────────────────────────────────────────────┐
│  CENTER UI (port 80)                                 │
│  ┌───────────────────────────────────────────────┐  │
│  │  User Management Page                          │  │
│  │  - List/Create/Edit/Delete users               │  │
│  │  - Assign roles (admin/engineer/operator)       │  │
│  │  - Assign Edge access (per-edge toggle)         │  │  NEW
│  │  - Push users to Edge nodes                     │  │  NEW
│  └───────────────────────────────────────────────┘  │
│                         │                            │
│  ┌───────────────────────────────────────────────┐  │
│  │  Backend (port 8000)                           │  │
│  │  ┌─────────────┐  ┌─────────────────────────┐ │  │
│  │  │ users table  │  │ edge_user_assignments   │ │  │  NEW
│  │  │ (PostgreSQL) │  │ edge_node_id → user_ids │ │  │
│  │  └─────────────┘  └─────────────────────────┘ │  │
│  │                                               │  │
│  │  POST /api/v1/users               (CRUD)      │  │  FIX
│  │  POST /api/v1/edges/{id}/users     (assign)    │  │  NEW
│  │  POST /api/v1/edges/{id}/users/sync (push)    │  │  NEW
│  └───────────────────────────────────────────────┘  │
└──────────────────────┬──────────────────────────────┘
                       │ HTTP (Center → Edge)
                       ▼
┌─────────────────────────────────────────────────────┐
│  EDGE v2 (port 8011)                                 │
│  ┌───────────────────────────────────────────────┐  │
│  │  GET /api/auth/users/sync  (pull from Center)  │  │  NEW
│  │  POST /api/auth/users       (receive push)     │  │  NEW
│  │                                               │  │
│  │  LocalUserStore (SQLite or config YAML)        │  │  NEW
│  │  - Cached copy of authorized users             │  │
│  │  - Sync on startup + periodic refresh           │  │
│  │  - Supports offline login (cached creds)        │  │
│  └───────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

### 2.3 Data Flow

```
CREATE USER:
  Center UI → POST /api/v1/users → PostgreSQL users table
  → Admin clicks "Assign to Edge X"
  → POST /api/v1/edges/{id}/users/sync → Edge API
  → Edge stores in local user cache

LOGIN ON EDGE:
  User enters credentials on Edge UI
  → Edge checks local cache first (fast, offline-capable)
  → If not found, optionally validates against Center API (online fallback)
  → Session created on Edge (signed cookie)

SYNC ON EDGE STARTUP:
  Edge starts → GET /api/auth/users/sync?from=last_sync_ts
  → Center returns user list for this edge
  → Edge updates local cache
```

### 2.4 Database Changes

**New table: `edge_user_assignments` (PostgreSQL, Center only)**

```sql
CREATE TABLE edge_user_assignments (
    id UUID PRIMARY KEY,
    edge_node_id VARCHAR(128) NOT NULL,  -- e.g., "EDGEV2-PC-01"
    user_id UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(edge_node_id, user_id)
);
```

### 2.5 API Contract

#### Center — NEW endpoints

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/api/v1/edges/{edge_node_id}/users` | admin | Assign user to edge |
| DELETE | `/api/v1/edges/{edge_node_id}/users/{user_id}` | admin | Remove assignment |
| GET | `/api/v1/edges/{edge_node_id}/users` | admin | List assigned users |
| POST | `/api/v1/edges/{edge_node_id}/users/sync` | admin | Push user list to edge |
| GET | `/api/v1/edges/{edge_node_id}/users/export` | admin | Get user list for edge sync (used by edge) |

#### Edge v2 — NEW endpoints

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/api/auth/users` | admin | List local cached users |
| POST | `/api/auth/users/sync` | Center API key or JWT | Receive user list from Center |
| GET | `/api/auth/users/sync` | Edge internal | Pull user list from Center |

### 2.6 Edge v2 LocalUserStore

```python
class LocalUserStore:
    """Local cache of authorized users, synced from Center."""
    
    def __init__(self, config):
        # Store in SQLite or config YAML
        # Format: {username: {password_hash, display_name, role, synced_at}}
        pass
    
    def authenticate(self, username: str, password: str) -> bool
    def list_users(self) -> list[UserInfo]
    def sync_from_center(self, center_users: list) -> None
    def sync_to_center(self) -> None  # pull
```

---

## 3. Implementation Plan

### Phase 1: Fix Center Users Page (P0 — 5 min)

**File:** `backend/app/api/v1.py`

```python
# ADD import:
from app.modules.users.router import router as users_router

# ADD include_router:
router.include_router(users_router, tags=["Users"])
```

**Verify:** `curl /api/v1/users` → 200 with user list

### Phase 2: Multi-User Edge v2 (P1)

**Files to modify:**
- `edge-v2/agent/auth/auth.py` — `LocalAuthManager` → support multiple users
- `edge-v2/agent/auth/local_user_store.py` — NEW: local user cache
- `edge-v2/agent/web/routes/auth.py` — login for multiple users
- `edge-v2/agent/config/config.edge-v2.yaml` — user storage format

**Changes:**
- `verify_password()` → lookup in user list, not just admin_hash
- `create_session()` → include role from user record
- Add `/api/auth/users` CRUD (admin only, local)
- Add `/api/auth/users/sync` — receive from Center

### Phase 3: Center ↔ Edge Sync (P1)

**Files to create:**
- `backend/app/modules/edge_users/router.py` — NEW
- `backend/app/modules/edge_users/models.py` — NEW (edge_user_assignments table)
- `backend/migrations/versions/005_edge_user_assignments.py` — NEW

**Files to modify:**
- `backend/app/api/v1.py` — register edge_users router
- `edge-v2/agent/main.py` — sync users on startup

### Phase 4: Center UI Enhancement (P2)

**Files to modify:**
- `frontend/src/features/users/UserManagementPage.tsx` — add "Edge Access" column + assign modal

---

## 4. Rollout Strategy

| Phase | Scope | Risk |
|---|---|---|
| Phase 1 | Fix Users API registration | None — 1 line import |
| Phase 2 | Edge v2 multi-user | Medium — auth change, test thoroughly |
| Phase 3 | Center-Edge sync | Medium — new API, new DB table |
| Phase 4 | UI enhancement | Low — pure frontend |

---

## 5. Open Questions

1. **Edge offline auth:** How long should cached credentials be valid without Center sync? (Proposal: 7 days)
2. **Password sync direction:** If user changes password on Edge, should it sync back to Center? (Proposal: No — Center is source of truth)
3. **Edge v1 support:** Should we backport multi-user to Edge v1? (Proposal: No — v1 is being phased out)
4. **Role mapping:** Center roles (admin/engineer/operator) → Edge roles? (Proposal: Same roles, admin=full, engineer=config, operator=read-only)

---

## 6. Recommendation

**Go with Phase 1 immediately** — fix the Users page (1 line, 5 minutes).

**Proceed with Phase 2+3 as a single prompt** — the Edge multi-user + Center sync are tightly coupled and should be implemented together.

**Phase 4 can follow after** — UI enhancement is lower priority.
