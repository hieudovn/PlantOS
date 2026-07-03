# Security Hardening — Bước 3: Frontend Credentials

## Context

Step 1+2 done. Center uses new credentials. Edge Agent uses `${EDGE_API_KEY}`. Now the frontend must stop using the hardcoded `{EDGE_API_KEY}` and use `FRONTEND_DEMO_KEY` from a build-time environment variable instead.

## ⚠️ SAFETY

- **DO NOT deploy to VPS yet.**
- Frontend must work BOTH with JWT (logged in) AND API key (MVP demo mode)
- The key MUST be injected at build time via Vite env vars, NOT hardcoded in source

## Required Reading

```text
frontend/src/lib/api.ts              ← Current: hardcoded API key at line 13
frontend/.env                         ← Does NOT exist — needs VITE_API_KEY
frontend/vite.config.ts              ← Vite config (check env var handling)
```

---

## Implementation

### Step 1: Create `frontend/.env`

```env
# Frontend demo API key — injected at build time by Vite
# Must match FRONTEND_DEMO_KEY in deployment/.env
VITE_API_KEY=plantos-frontend-<same-value-as-.env>
```

> **Note:** Get `FRONTEND_DEMO_KEY` from `deployment/.env`. Both must match.

### Step 2: Update `frontend/src/lib/api.ts`

Replace hardcoded key with Vite env var:

```typescript
// BEFORE (line 13):
headers["X-API-Key"] = "{EDGE_API_KEY}";

// AFTER:
// Use build-time injected key for MVP demo mode.
// In production, JWT token should always be present.
const DEMO_API_KEY = import.meta.env.VITE_API_KEY || "";
if (!token && DEMO_API_KEY) {
  headers["X-API-Key"] = DEMO_API_KEY;
}
```

### Step 3: Verify Build

```bash
cd frontend
npm run build
```

Check the built JS to confirm the old key is gone:

```bash
grep -c "{EDGE_API_KEY}" dist/assets/*.js
# Expected: 0
```

Check the new key IS present:

```bash
grep -c "plantos-frontend" dist/assets/*.js
# Expected: 1 (the new key from VITE_API_KEY)
```

### Step 4: Add `.env` to `.gitignore` if not already

```bash
echo "frontend/.env" >> .gitignore
```

---

## Deliverables

1. `frontend/.env` — `VITE_API_KEY=plantos-frontend-xxx` (matches deployment/.env)
2. Updated `frontend/src/lib/api.ts` — `import.meta.env.VITE_API_KEY` instead of hardcoded string

## Acceptance Criteria

- [ ] No `{EDGE_API_KEY}` in built JS
- [ ] `VITE_API_KEY` is read from `.env` at build time
- [ ] Frontend works without JWT (MVP demo mode with new key)
- [ ] Frontend works WITH JWT (logged in mode, key not used)
- [ ] `frontend/.env` is in `.gitignore`
