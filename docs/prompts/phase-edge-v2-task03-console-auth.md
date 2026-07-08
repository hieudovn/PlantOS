# E2V2-1: Local Console + Auth

## Context

Edge v2 needs local authentication and a product-grade console UI. Currently Edge v1 has NO auth on any API endpoint, `/api/config` exposes raw secrets, and the UI is inline HTML in Python strings. This phase builds a clean LocalAuthManager, session-based auth middleware, and 6 console pages (login, dashboard, signals, sync, logs, settings) as separate static HTML/CSS/JS files with shared PlantOS design tokens.

## Plan Reference

- `docs/phase-edge-v2-productization-plan.md` §8, §12
- `docs/01-project-constitution.md`
- `docs/60-edge-center-strategy.md`

## Constitution Checklist

- [x] Does NOT bypass UNS/CDM
- [x] Does NOT bind UI to raw PLC tags
- [x] Does NOT let UI query storage directly (all through /api/*)
- [x] Security by design (auth, session, CSRF, sanitization)
- [x] No secrets in logs or config output

## Implementation Checklist

### Auth Backend

- [ ] **1.1** Implement `LocalAuthManager` in `edge-v2/agent/auth/auth.py`:
  - `create_admin(password: str)` — bcrypt hash, store in config
  - `verify_password(username: str, password: str) -> bool`
  - `change_password(old: str, new: str) -> bool`
  - `is_first_run() -> bool` — detect if no admin password set
  - `create_session(username: str, role: str) -> str` — signed cookie (itsdangerous)
  - `validate_session(cookie: str) -> Session | None`
  - `destroy_session(cookie: str)`
  - Roles: `viewer`, `admin`

- [ ] **1.2** Implement auth middleware in `edge-v2/agent/auth/middleware.py`:
  - aiohttp middleware that checks session cookie on all `/api/*` routes
  - Exempt: `/api/auth/login`, `/api/auth/setup`, `/api/status` (health check)
  - Return 401 JSON if invalid/missing session
  - Inject `request.user` with `{username, role}` for downstream handlers

- [ ] **1.3** Create auth API routes in `edge-v2/agent/web/routes/auth.py`:
  - `POST /api/auth/setup` — first-run admin password creation (only if no admin exists)
  - `POST /api/auth/login` — verify credentials, set session cookie, return `{role, redirect}`
  - `POST /api/auth/logout` — clear session cookie
  - `POST /api/auth/change-password` — verify old, set new, require re-login
  - `GET /api/auth/me` — return current user info from session

- [ ] **1.4** Sanitize `/api/config`:
  - Remove: `api_key`, `password_secret_ref`, `local_admin_hash`, `session_secret_ref`
  - Replace with `"***REDACTED***"`
  - Return all other config fields normally
  - Write test to verify no secrets leak

- [ ] **1.5** Add CSRF protection:
  - Generate CSRF token on login, store in session
  - Require `X-CSRF-Token` header on all POST/PUT/DELETE endpoints
  - Return 403 if missing/mismatched

- [ ] **1.6** Create `WebServer` class in `edge-v2/agent/web/server.py`:
  - Clean rewrite (NOT copied from v1 `web.py`)
  - Constructor accepts: config, auth, buffer, connectors, processing, sync
  - No global module variables
  - Register all route handlers
  - Serve static files from `edge-v2/console/static/`

### Console UI

- [ ] **1.7** Create shared design tokens:
  - `console/static/css/plantos-tokens.css` — colors, fonts, spacing, cards, tables
  - Match Center design language (blue primary, dark sidebar, card-based layout)
  - Responsive layout (works on 1024px+ screens)

- [ ] **1.8** Create shared JS modules:
  - `console/static/js/api.js` — `fetch()` wrapper with auth headers, CSRF
  - `console/static/js/auth.js` — login check, redirect if unauthenticated
  - `console/static/js/nav.js` — dynamic navigation header injection

- [ ] **1.9** Create `login.html`:
  - Username + password form
  - "First time? Create admin password" flow (redirects to setup)
  - Error display for invalid credentials
  - Redirect to dashboard on success

- [ ] **1.10** Create `dashboard.html`:
  - Status cards: Agent Status, Center Connection, Connector Status (placeholder)
  - Buffer stats: row count, size, retention
  - Sync stats: backlog, last sync, failed count
  - Recent signals table (last 20 values)
  - Auto-refresh every 5 seconds via `/api/status` + `/api/measurements/latest`
  - Version + uptime footer

- [ ] **1.11** Create `signals.html`:
  - Table: Signal ID, Value, Quality, Timestamp
  - Filter by quality (GOOD/STALE/BAD)
  - Search by signal_id
  - Auto-refresh every 5 seconds

- [ ] **1.12** Create `sync.html`:
  - Center URL + connection status
  - Last heartbeat time + status
  - Last sync time + accepted/rejected counts
  - Backlog count + dead letter count
  - Sync interval + batch size display
  - "Sync Now" button (placeholder for now)

- [ ] **1.13** Create `logs.html`:
  - Log display area (scrollable)
  - Filter by severity: All, INFO, WARN, ERROR
  - Filter by source: agent, connector, sync
  - Time range: Last 15min, 1hr, 6hr, 24hr
  - "Download Recent Logs" button (placeholder)

- [ ] **1.14** Create `settings.html`:
  - Edge identity: node_id, site, plant (read-only from config)
  - Center URL + API key status (masked)
  - Change password form
  - Config ownership status (local-owned vs center-owned, placeholder)
  - "Export Sanitized Config" button

### Tests

- [ ] **1.15** Auth flow tests:
  - Login with valid credentials → 200 + session cookie
  - Login with invalid credentials → 401
  - Access protected endpoint without cookie → 401
  - Access protected endpoint with valid cookie → 200
  - Logout → cookie cleared, subsequent access → 401
  - First-run setup → admin created, subsequent setup disabled

- [ ] **1.16** API protection tests:
  - All `/api/*` endpoints return 401 without auth (except login/setup/status)
  - Viewer role cannot access admin endpoints
  - Admin role can access all endpoints

- [ ] **1.17** Config sanitization tests:
  - Verify `/api/config` does not contain: api_key, password, secret, hash
  - Verify other config fields are present and correct

## Files to Create

```
edge-v2/agent/
  auth/
    __init__.py
    auth.py
    middleware.py
  web/
    __init__.py
    server.py
    routes/
      __init__.py
      auth.py
      status.py
      config.py

edge-v2/console/static/
  css/plantos-tokens.css
  js/api.js
  js/auth.js
  js/nav.js
  login.html
  dashboard.html
  signals.html
  sync.html
  logs.html
  settings.html

edge-v2/tests/
  test_auth.py
  test_config_sanitization.py
```

## Files to Modify

- `edge-v2/agent/main.py` — wire LocalAuthManager and WebServer
- `edge-v2/agent/config/config.edge-v2.yaml` — add auth section

## Acceptance Criteria

```text
✅ No unauthenticated access to /api/* (except login/setup/status)
✅ Login/logout works with session cookie
✅ First-run forces password setup before any page loads
✅ Dashboard shows live edge status (buffer, sync, signals)
✅ /api/config does not expose passwords, API keys, or hashes
✅ CSRF protection on all state-changing endpoints (POST/PUT/DELETE)
✅ Viewer role cannot access settings/connections write endpoints
✅ Admin role can access all endpoints
✅ All UI pages share consistent design tokens
✅ No inline HTML in Python files
```

## Red Flags

- Stop if: auth implementation stores plaintext passwords
- Stop if: `/api/config` leaks any secrets
- Stop if: session cookie is not HttpOnly
- Stop if: constitution violation (raw DB access from UI, bypassing API)
