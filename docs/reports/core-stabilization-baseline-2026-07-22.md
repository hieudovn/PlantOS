# Core Stabilization Baseline — 2026-07-22

> **Commit:** `ae8b611` | **Branch:** `main` | **Timestamp:** 2026-07-22 17:04:16 +0700

---

## 1. Executive Summary

Baseline established from clean `main` commit `ae8b611`. Working tree has 18 untracked temp files from E2V2-14 Coder execution (not committed). VPS is running `plantos-edge-v2:patched` image built 2026-07-13 — **9 days of runtime drift**. Config was hot-patched via `docker cp` (not from image).

**Critical findings:** 14 TypeScript errors block clean build. Hardcoded password in `edge-v2/agent/main.py:237`. 7 ports publicly exposed. Edge v2 image 9 days stale. VPS git repo on different commit.

**Recommendation:** NO-GO for Phase 8 execution until P0 items resolved.

---

## 2. Exact Baseline

| Parameter | Value |
|---|---|
| Repository | github.com/hieudovn/PlantOS |
| Branch | `main` |
| Commit SHA | `ae8b61108984de8bf03809e07a656ed1a6f1812e` |
| Commit time | 2026-07-22T10:04:16Z |
| Working tree | Clean (18 untracked temp files) |
| Local OS | Windows (PowerShell) |
| VPS OS | Ubuntu 22.04.5 LTS |
| VPS Docker | 29.5.3 |
| VPS Python | 3.10.12 |
| VPS Node | v20.20.2, npm 10.8.2 |

## 3. Runtime/Source Drift

| Component | Source (git) | Runtime (VPS) | Drift |
|---|---|---|---|
| Edge v2 config | `edge-v2/agent/config/config.edge-v2.yaml` | `/app/config/config.edge-v2.yaml` (container) | ⚠️ Hot-patched: batch_size=500, connector type fixed |
| Edge v2 image | Not in repo | `plantos-edge-v2:patched` built 2026-07-13 | 🔴 9 days old, not rebuilt from HEAD |
| VPS git | `ae8b611` (main) | `692f93c` (different branch) | 🔴 VPS repo on unrelated commit |
| Backend image | `deployment-backend:latest` | Built 2 weeks ago | ⚠️ Not rebuilt for users router fix |
| Frontend image | `deployment-frontend:latest` | Built 2 weeks ago | ⚠️ Served via host nginx from dist/ |

**Drift Status:** SIGNIFICANT — Edge v2 running patched image with manual config fixes. Not reproducible from source.

---

## 4. Clean Build Results

### 4.1 Frontend — FAILED

```
Command: npm run build (tsc && vite build)
Result: 14 TypeScript errors in 10 files
```

| # | File | Line | Error | Source |
|---|---|---|---|---|
| 1 | TrendBundle.tsx | 88 | `showLegend` prop not in Props | Pre-existing |
| 2 | AssetBindings.tsx | 32 | Expected 1 arg, got 2 | Pre-existing |
| 3 | AssetBindings.tsx | 40 | Expected 1 arg, got 2 | Pre-existing |
| 4 | AssetForm.tsx | 19 | Expected 0 args, got 1 | Pre-existing |
| 5 | KpiDefinitionsPage.tsx | 19 | Expected 0 args, got 1 | Pre-existing |
| 6-8 | AssetConditionView.tsx | 28,30 | Implicit `any` (s, i) | 🔴 From refactoring |
| 9 | AssetCard.tsx | 19 | Cannot find `ThresholdConfig` | 🔴 From refactoring |
| 10 | ConditionScoreCard.tsx | 24 | Cannot find `ThresholdConfig` | 🔴 From refactoring |
| 11 | KeySignalsCard.tsx | 6 | Cannot find `AssetSignalConfig` | 🔴 From refactoring |
| 12 | KeySignalsCard.tsx | 9 | Cannot find `ThresholdConfig` | 🔴 From refactoring |
| 13 | ProcessBlock.tsx | 32 | Cannot find `ThresholdConfig` | 🔴 From refactoring |
| 14 | useAssetSignals.ts | 16 | `data` property on never | 🔴 From refactoring |

**Note:** Errors 6-14 were introduced by the hardcode refactoring. Need to add proper type imports or remove type annotations.

### 4.2 Backend — NOT_VERIFIED

```
Cannot run in current environment (Windows, no venv).
Required commands:
  cd backend
  python -m venv .venv
  pip install -e ".[dev]"
  python -c "from app.main import app; print('IMPORT_OK')"
  alembic upgrade head
  pytest -q
```

### 4.3 Edge v2 — NOT_VERIFIED

```
No pytest available in current environment.
Required commands:
  pytest edge-v2/tests -q
  docker build -f edge-v2/Dockerfile .
```

### 4.4 Docker Compose — NOT_VERIFIED

```
Docker Compose not available in local environment.
VPS has docker compose but running different config.
```

---

## 5. Network Exposure

Collected from VPS `ss -lntup`:

| Port | Bind | Service | Public? | Risk |
|---|---|---|---|---|
| 80 | 0.0.0.0 | nginx (Center UI) | ✅ Public | 🟡 No HTTPS |
| 22 | 0.0.0.0 | SSH | ✅ Public | 🟢 Standard |
| 8011 | 0.0.0.0 | Edge v2 Web | ✅ Public | 🔴 No HTTPS, default session_secret |
| 9998 | 0.0.0.0 | HTTP Simulator | ✅ Public | 🔴 Should be internal only |
| 9999 | 0.0.0.0 | Test HTTP Server | ✅ Public | 🔴 Should not be running |
| 4840 | 0.0.0.0 | OPC UA (VF) | ✅ Public | 🟡 Industrial protocol exposed |
| 4841 | 0.0.0.0 | OPC UA | ✅ Public | 🟡 Industrial protocol exposed |
| 7000 | 0.0.0.0 | Unknown service | ✅ Public | 🔴 Unknown exposure |
| 8002 | 0.0.0.0 | Virtual Factory | ✅ Public | 🟡 Dev service |
| 8100 | 0.0.0.0 | Unknown Python | ✅ Public | 🔴 Unknown exposure |
| 8000 | 127.0.0.1 | Backend API | Internal | 🟢 OK |
| 5432 | 127.0.0.1 | PostgreSQL | Internal | 🟢 OK |
| 6041 | 127.0.0.1 | TDengine | Internal | 🟢 OK |
| 1883 | 127.0.0.1 | MQTT | Internal | 🟢 OK |
| 6030 | 127.0.0.1 | TDengine REST | Internal | 🟢 OK |
| 18083 | 127.0.0.1 | EMQX Dashboard | Internal | 🟢 OK |

**Target topology:** Only ports 80 and 22 should be public. Edge v2 (8011) via nginx reverse proxy with HTTPS.

---

## 6. Security Findings Summary

### CRITICAL

| ID | Finding | File | Line |
|---|---|---|---|
| SEC-001 | Hardcoded Center password in Edge v2 JWT login | `edge-v2/agent/main.py` | 237 |
| SEC-002 | 7 ports publicly exposed beyond nginx+SSH | VPS network | — |

### HIGH

| ID | Finding | File |
|---|---|---|
| SEC-003 | No HTTPS on public ports 80, 8011 | nginx config |
| SEC-004 | Default session_secret `super-secret-key-change-in-production` | `config.edge-v2.yaml` |
| SEC-005 | Default API key `plantos-edge-key-2026` in deployment | `docker-compose.yml` |
| SEC-006 | Public Edge v2 Web without TLS | VPS port 8011 |

### MEDIUM

| ID | Finding | File |
|---|---|---|
| SEC-007 | Password hashes sent to Edge via sync API without TLS | `edge_users/router.py` |
| SEC-008 | `innerHTML` usage in `nav.js` — potential DOM XSS | `edge-v2/console/static/js/nav.js` |
| SEC-009 | EMQX unhealthy, potential security patch missing | Docker |
| SEC-010 | No rate limiting on login endpoints | Backend + Edge v2 |
| SEC-011 | `show_index=False` but no root redirect | `edge-v2/agent/web/server.py` |

---

## 7. Code Quality Findings

| ID | Severity | Finding |
|---|---|---|
| CQ-001 | MEDIUM | `ThresholdConfig` type removed but still referenced in 5 files |
| CQ-002 | MEDIUM | `AssetSignalConfig` type import missing from `KeySignalsCard` |
| CQ-003 | MEDIUM | Implicit `any` types in `AssetConditionView` |
| CQ-004 | LOW | 18 untracked temp Coder scripts in working tree |
| CQ-005 | LOW | `TODO` in `modbus/connector.py:178` |
| CQ-006 | MEDIUM | Dual config paths in Edge v2 container |
| CQ-007 | LOW | `PLANT_CONFIGS` deprecated but plant config files still exist |
