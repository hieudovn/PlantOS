# Runtime / Source Drift Report — 2026-07-22

> **Source commit:** `ae8b611` (main)
> **VPS runtime snapshot:** 2026-07-22T10:22:59Z

---

## 1. VPS Git vs Source Git

| Item | Source (ae8b611) | VPS (/opt/plantos) | Match? |
|---|---|---|---|
| HEAD | `ae8b611` | `692f93c` | ❌ |
| Message | SA review report | Test OPC UA integration | ❌ |
| Date | 2026-07-22 | ~2026-06 (estimated) | ❌ |

**Assessment:** VPS repo has not been updated since June. All deployments done via manual file copy + docker cp, not git pull + rebuild.

---

## 2. Edge v2 Image Drift

| Parameter | Value |
|---|---|
| Running image | `plantos-edge-v2:patched` |
| Built | 2026-07-13T06:04:54Z |
| Age | 9 days |
| Source commit at build | Unknown (not tagged in image) |
| Hotfixes applied | batch_size=500, connector type=http_poll (docker cp) |
| Config path | `/app/config/config.edge-v2.yaml` (not `/app/agent/config/`) |

**If container restarts:** Config hotfixes persist (file was updated in container). If container is recreated from image: hotfixes LOST — old config restored.

---

## 3. Backend Image Drift

| Item | Value |
|---|---|
| Image | `deployment-backend:latest` |
| Built | ~2 weeks ago |
| Users router | Registered? UNKNOWN — VPS api/v1.py not checked |
| Edge users module | `/api/v1/edges/{id}/users` — CODED, deployed via docker cp |

**Risk:** On container recreate, users router registration lost if `v1.py` wasn't in the image.

---

## 4. Frontend Serving

| Layer | Detail |
|---|---|
| Container | `deployment-frontend:latest` (Vite dev server, port 5173) |
| Actual serving | Host nginx from `/opt/plantos/frontend/dist/` |
| Last dist deploy | 2026-07-13 (manual SCP + nginx reload) |
| Drift | Container image stale, but dist/ served directly |

**Risk:** Dist files from 2026-07-13 may not match current source.

---

## 5. Config Drift Summary

| Config | Source | Runtime | Drift |
|---|---|---|---|
| `config.edge-v2.yaml` | `edge-v2/agent/config/` | `/app/config/` (different path!) | ⚠️ Path mismatch |
| `publish.batch_size` | 10 (in source) | 500 (hot-patched) | ⚠️ Not in source |
| `publish.interval_seconds` | 10 (in source) | 5 (hot-patched) | ⚠️ Not in source |
| `mirror_wtp_signals.type` | http_poll (source) | http_poll (patched) | ✅ (was missing, now fixed) |
| `plant_id` | EDGEV2-DEMO (source) | DEMO-PLANT (hot-patched) | ⚠️ E2V2-14 change |
| `session_secret` | CHANGE_ME (source) | super-secret-key... (patched) | ⚠️ |
| `api_key` | plantos-edge-key-2026 | plantos-edge-key-2026 | ✅ Same (still default) |

---

## 6. Conclusion

**Significant drift exists.** The running system cannot be reproduced from the source commit alone. Hotfixes applied via docker cp are not traceable to git. A container restart from image would revert config changes.

**Required action:** Rebuild Edge v2 image from HEAD with all config changes committed to source.
