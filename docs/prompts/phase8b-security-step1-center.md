# Security Hardening — Bước 1: New Credentials + Center Config

## Context

You are the Coder-Executioner for PlantOS Security Hardening.

The current system uses hardcoded default credentials everywhere. Your job in Step 1 is to create new, strong credentials and configure the Center backend to use them. Steps 2-5 (Edge Agent, Frontend, Tools, Docs) will follow in separate tasks.

## ⚠️ CRITICAL SAFETY RULES

1. **DO NOT change anything on the running VPS production system.** This task only modifies the LOCAL codebase. Deployment will happen in a separate step after all code is reviewed.
2. **Do NOT break the local dev environment.** After changes, `docker compose up` must still work with the new `.env` file.
3. **Keep backward compatibility for dev.** If `.env` is missing, provide clear error messages, not crashes.
4. **Never commit the `.env` file.** It's already in `.gitignore`.

## Required Reading

```text
backend/app/core/config.py               ← All default credentials live here
backend/app/middleware/auth.py            ← DEBUG bypass must be fixed
backend/app/db/tdengine.py                ← TDengine connection
deployment/docker-compose.yml             ← Service definitions with env vars
deployment/env.example                    ← Template (update with placeholders)
```

---

## Implementation Checklist

### Step 1: Create `deployment/.env` from `env.example`

Read the current `deployment/env.example`. Create a new `deployment/.env` with REAL random values:

```bash
# Generate random values (run these, paste results into .env)
python -c "import secrets; print('POSTGRES_PASSWORD=' + secrets.token_urlsafe(16))"
python -c "import secrets; print('TDENGINE_PASSWORD=' + secrets.token_urlsafe(12))"
python -c "import secrets; print('JWT_SECRET=' + secrets.token_urlsafe(24))"
python -c "import secrets; print('EDGE_API_KEY=plantos-edge-' + secrets.token_hex(12))"
python -c "import secrets; print('FRONTEND_DEMO_KEY=plantos-frontend-' + secrets.token_hex(12))"
python -c "import secrets; print('MQTT_PASSWORD=' + secrets.token_urlsafe(12))"
```

The `.env` file must contain:

```env
# ============================================
# PlantOS Security Credentials
# Generated: 2026-07-03
# ============================================

# PostgreSQL
POSTGRES_USER=plantos
POSTGRES_PASSWORD=<24-char random>
POSTGRES_DB=plantos

# TDengine
TDENGINE_USER=root
TDENGINE_PASSWORD=<16-char random>

# JWT
JWT_SECRET=<32-char random>

# API Keys (for internal service-to-service auth)
EDGE_API_KEY=plantos-edge-<24-hex>
FRONTEND_DEMO_KEY=plantos-frontend-<24-hex>

# MQTT
MQTT_USER=edge-agent
MQTT_PASSWORD=<16-char random>

# App
DEBUG=false
ENVIRONMENT=production
```

### Step 2: Update `deployment/docker-compose.yml`

Change ALL services to read from env vars WITHOUT hardcoded fallbacks:

**PostgreSQL:**
```yaml
# BEFORE:
POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-plantos}
# AFTER:
POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:?POSTGRES_PASSWORD must be set in .env}
```

**TDengine:**
```yaml
# BEFORE:
TAOS_PASSWORD: ${TDENGINE_PASSWORD:-taosdata}
# AFTER:
TAOS_PASSWORD: ${TDENGINE_PASSWORD:?TDENGINE_PASSWORD must be set in .env}
```

**Backend service:**
```yaml
# BEFORE:
JWT_SECRET: ${JWT_SECRET:-plantos-dev-secret-change-in-production}
API_KEYS: ${API_KEYS:-{EDGE_API_KEY}}
# AFTER:
JWT_SECRET: ${JWT_SECRET:?JWT_SECRET must be set in .env}
API_KEYS: ${EDGE_API_KEY},${FRONTEND_DEMO_KEY}
```

**EMQX (add auth):**
```yaml
emqx:
  environment:
    EMQX_ALLOW_ANONYMOUS: "false"
    EMQX_MQTT__MAX_PACKET_SIZE: 10MB
```

### Step 3: Update `backend/app/core/config.py`

Remove ALL hardcoded credential defaults. Replace with `""` or throw clear errors:

```python
# BEFORE:
POSTGRES_PASSWORD: str = "plantos"
TDENGINE_PASSWORD: str = "taosdata"
JWT_SECRET: str = "plantos-dev-secret-change-in-production"

# AFTER:
POSTGRES_PASSWORD: str = ""  # Required — set via POSTGRES_PASSWORD env var
TDENGINE_PASSWORD: str = ""  # Required — set via TDENGINE_PASSWORD env var
JWT_SECRET: str = ""         # Required — set via JWT_SECRET env var
```

Add a startup validation in `backend/app/main.py` or `backend/app/core/config.py`:

```python
# At startup, validate required settings
if not settings.JWT_SECRET or settings.JWT_SECRET.startswith("plantos-dev"):
    raise RuntimeError("JWT_SECRET is not set or is using the default insecure value. Set it in .env")
if not settings.API_KEYS:
    raise RuntimeError("API_KEYS is empty. At least one API key must be configured for internal service auth.")
```

### Step 4: Fix `backend/app/middleware/auth.py` — Remove DEBUG Bypass

```python
# BEFORE (line 22-23):
if settings.DEBUG:
    return await call_next(request)

# AFTER:
if settings.DEBUG:
    logger.warning("AUTH BYPASS: DEBUG mode is ON — all requests are unauthenticated. "
                   "This should NEVER happen in production.")
    return await call_next(request)
```

Keep the bypass for local dev, but ADD A LOUD WARNING so it can't be accidentally left on in production.

### Step 5: Update EMQX Auth in docker-compose

Add authentication config to EMQX. The easiest way without external config files:

```yaml
emqx:
  image: emqx/emqx:5.7.0
  environment:
    EMQX_ALLOW_ANONYMOUS: "false"
    EMQX_DASHBOARD__DEFAULT_USERNAME: admin
    EMQX_DASHBOARD__DEFAULT_PASSWORD: ${MQTT_PASSWORD:?MQTT_PASSWORD must be set}
```

For MQTT client auth, we'll set it up when updating the Edge Agent (Step 3 of the Security Plan).

### Step 6: Update `deployment/env.example`

Replace ALL hardcoded values with `change-me` placeholders:

```env
POSTGRES_PASSWORD=change-me
TDENGINE_PASSWORD=change-me
JWT_SECRET=change-me
EDGE_API_KEY=plantos-edge-change-me
FRONTEND_DEMO_KEY=plantos-frontend-change-me
MQTT_PASSWORD=change-me
```

### Step 7: Verify Local Dev Still Works

After changes, test:

```bash
# 1. Start with new .env
cd deployment
docker compose down
docker compose up -d postgres tdengine emqx

# 2. Check all services healthy
docker compose ps

# 3. Start backend (should NOT crash from missing env vars)
cd ../backend
pip install -e ".[dev]"
uvicorn app.main:app --host 0.0.0.0 --port 8000 &
sleep 3
curl http://localhost:8000/health

# 4. Test with new API key
curl http://localhost:8000/api/v1/plants \
  -H "X-API-Key: $(grep EDGE_API_KEY ../deployment/.env | cut -d= -f2)"

# 5. Stop
kill %1
docker compose down
```

## Deliverables

1. `deployment/.env` — Real random credentials (NEVER COMMIT THIS)
2. `deployment/.env.example` — Updated with `change-me` placeholders
3. `deployment/docker-compose.yml` — Env vars with `:?` fail-fast, EMQX auth
4. `backend/app/core/config.py` — No hardcoded credential defaults
5. `backend/app/middleware/auth.py` — DEBUG bypass with loud warning

## Files NOT to touch in Step 1

- ❌ `edge/agent/config.yaml` (will be Step 2)
- ❌ `frontend/src/lib/api.ts` (will be Step 3)
- ❌ `tools/*.py` (will be Step 4)
- ❌ VPS running system (deploy after all steps done)

## Acceptance Criteria

- [ ] `docker compose up` succeeds with new `.env`
- [ ] `POSTGRES_PASSWORD`, `TDENGINE_PASSWORD`, `JWT_SECRET` have no hardcoded defaults
- [ ] `API_KEYS` reads from `EDGE_API_KEY,FRONTEND_DEMO_KEY` env vars
- [ ] DEBUG bypass still works but logs a warning
- [ ] EMQX anonymous access is disabled
- [ ] `.env` contains real random credentials (not `change-me`)
- [ ] Backend starts without crash, `/health` returns 200
- [ ] Old hardcoded key `{EDGE_API_KEY}` is NOT in any of the 5 modified files
