# PlantOS Edge v2 — Phase E2V2-7 PM Review Report for SA

> **Date:** 2026-07-09
> **Author:** PM-Designer (DeepSeek V4 Pro)
> **Review Scope:** EV2-STAB + E2V2-7 (a/b/c) full codebase audit
> **Status:** 7/12 execution tasks complete, 3 bugs found & fixed, 56 issues identified
> **SA Decision Needed:** Approve production-readiness gate plan

---

## 1. Executive Summary

Edge v2 Productization Track reached a major milestone. All 3 EV2-STAB gates passed (Data E2E, Command E2E, Docker Smoke). E2V2-7 mirror preparation is 7/12 complete with the most critical SA gate — **rollback dry-run** — verified (v1 unchanged after v2 stop/restart). Three code bugs were discovered and fixed during VPS execution testing, enabling data to flow end-to-end for the first time.

**56 code quality issues** were identified across 10 audited files (5 P0, 15 P1, 26 P2). Top concerns: hardcoded credentials in 4 files, missing safety gates for destructive operations, and zero test coverage for critical migration tooling.

---

## 2. Progress Status

### 2.1 EV2-STAB — ✅ CLOSED

| Gate | Status | Evidence |
|---|---|---|
| Data E2E | ✅ PASS | HTTP simulator → connector → processing → buffer (12.5 [GOOD]) |
| Command E2E | ✅ PASS | Center → Edge poll → execute sync_now → result |
| Docker Smoke | ✅ PASS | save/load workaround (VPS provider blocks Docker Hub), port 8011, healthy |

### 2.2 E2V2-7a (Artifacts) — ✅ DONE (7/7)

| Task | Status |
|---|---|
| Mirror config WTP + VF (29 tags) | ✅ |
| Config migration utility | ✅ |
| Data comparison tool | ✅ |
| Migration runbook (SA-aligned) | ✅ |
| Rollback runbook (SA-aligned) | ✅ |
| Seed test script | ✅ |
| Docker smoke | ✅ |

### 2.3 E2V2-7b (VPS Execution) — ⚠️ PARTIAL (3/5)

| Phase | Status | Details |
|---|---|---|
| Phase 1: Pre-flight | ✅ PASS | v1=200, v2=healthy, Center=200 |
| Phase 2: Side-by-side | ⚠️ Not meaningful | 0 shared signal_ids (v2 data not in Center yet) |
| Phase 3: Center offline | ✅ PASS | Backend stopped 5min → restored → health 200 |
| Phase 4: Dry-run migration | ⚠️ 401 auth | Seed script fixed (JWT login), not re-run |
| **Phase 5: Rollback dry-run** | **✅ PASS** | **v1 UNCHANGED after v2 stop/restart** |
| Phase 6: Report update | ⚠️ Encoding bug | Fixed (utf-8), not re-run |

### 2.4 E2V2-7c (Bug Fixes) — ✅ DONE (3/3)

| Bug | Root Cause | Fix |
|---|---|---|
| Buffer always 0 rows | `processing_loop` used `config.get()` instead of `connector.tags` | 1-line fix: `tag_configs = connector.tags` |
| HTTP Poll extraction failure | `_extract_value` split keys with dots (e.g., `PUMP-101.flow_rate` → wrong nested path) | Try flat key first, then fall back to dot-path |
| DuckDB crash (`pytz` missing) | `requirements.txt` missing `pytz` dependency | Added `pytz>=2024.1` |

**Verified:** Buffer row_count now increases ~0.3/sec (9 → 21 rows in 30s).

---

## 3. Changes Summary

### 3.1 Files Created (E2V2-7)

```
docs/prompts/phase-edge-v2-task09-migration.md       E2V2-7 original prompt (7/12 complete)
docs/prompts/phase-edge-v2-task09b-execution.md      E2V2-7b VPS execution prompt
docs/prompts/phase-edge-v2-task09c-bugfix.md         E2V2-7c bugfix prompt
docs/runbooks/edge-v1-to-v2-migration.md             Migration runbook (6 phases, 4-6 BLOCKED)
docs/runbooks/edge-v1-to-v2-rollback.md              Rollback runbook (7 steps)
docs/reports/edge-v2-stab-final-sa-review.md         EV2-STAB final report (3/3 gates)
docs/reports/edge-v2-migration-prep.md               E2V2-7 prep report
tools/vps_execute_e2v2_7b.py                         VPS execution script (6 phases, 343 lines)
tools/compare_v1_v2_data.py                          v1/v2 data comparison tool
tools/migrate_v1_config_to_v2.py                     Config migration utility
tools/http_simulator.py                              HTTP simulator for testing (port 9998)
tools/seed_edgev2_demo.py                            EDGEV2-DEMO workspace seed script
scripts/seed_edgev2_test.py                          EDGEV2-TEST workspace seed script
edge-v2/scripts/vps_phase2_check.sh                  Pre-flight check script
```

### 3.2 Files Modified

```
edge-v2/agent/main.py                    Line 166: config.get() → connector.tags
edge-v2/agent/connectors/http_poll/connector.py  Line 148: _extract_value flat-key fix
edge-v2/requirements.txt                 +pytz>=2024.1
edge-v2/Dockerfile                       Fixed COPY paths (edge-v2/ prefix), restored from a30dc4a
edge-v2/agent/config/config.edge-v2.yaml Merged mirror connectors, Docker fixes (buffer path, auth)
edge-v2/README.md                        MIRROR MODE notice, SA report link
```

---

## 4. Code Quality Audit — Key Findings

Full audit across 10 files identified **56 issues**: 5 P0, 15 P1, 26 P2.

### 4.1 Critical (P0) — Must Fix Before Production

| # | File | Issue |
|---|---|---|
| 1 | `vps_execute_e2v2_7b.py:11` | **Hardcoded password** `PlantOS@2026!` in source |
| 2 | `compare_v1_v2_data.py:39` | **Hardcoded credentials** `admin/PlantOS@2026!` |
| 3 | `seed_edgev2_test.py:30` | **Hardcoded password** in login call |
| 4 | `config.edge-v2.yaml:8` | **Default session_secret** — forgeable tokens, no startup refusal |
| 5 | `vps_execute_e2v2_7b.py:141` | **Destructive `docker stop`** on production without safety gate |

### 4.2 Hardcoding & Configuration Issues

| Pattern | Count | Examples |
|---|---|---|
| Hardcoded credentials | 4 files | Passwords, API keys in source |
| Hardcoded IPs/hosts | 2 files | `103.97.132.249`, `localhost` defaults |
| Hardcoded IDs | 2 files | `EDGEV2-PC-01`, `EDGEV2-DEMO` |
| Missing env var overrides | 6 files | No `.env` support in tools |

### 4.3 Error Handling

| Pattern | Count | Risk |
|---|---|---|
| Silent `except: pass` | 5+ places | Failures masked, impossible to debug |
| No retry on HTTP | 2 files | Single network glitch = zero data |
| Bare `except Exception` | 3 places | Catches `KeyboardInterrupt`, `CancelledError` |
| No `try/except` on JSON parse | 3 places | Crashes on non-JSON responses |

### 4.4 Testing

| Tool | Tests | Risk |
|---|---|---|
| `vps_execute_e2v2_7b.py` (343 lines) | 0 | Orchestration crashes silently in production |
| `compare_v1_v2_data.py` (210 lines) | 0 | Wrong comparison results with no detection |
| `migrate_v1_config_to_v2.py` (155 lines) | 0 | Migration data loss with no detection |
| `seed_edgev2_test.py` (114 lines) | 0 | Seed failures masked |
| `edge-v2/agent/main.py` | 0 | Processing failures masked |

### 4.5 Docker & Security

| Issue | Risk |
|---|---|
| Container runs as **root** | RCE = root access |
| No multi-stage build | Image 351MB, could be ~150MB |
| No `.dockerignore` | Build context may leak secrets |
| apt cache not cleaned | ~50MB bloat |
| Missing `ENV PYTHONPATH` | Import fragility across environments |

---

## 5. Risk Register (Updated)

| # | Risk | L | I | Mitigation | Status |
|---|---|---|---|---|---|
| R1 | Hardcoded credentials leak | Low | Critical | Move to env vars before production | **NEW** |
| R2 | Destructive script in wrong env | Low | Critical | Add safety gate flag | **NEW** |
| R3 | Zero test coverage for migration tools | Medium | High | Add tests before production switch | **NEW** |
| R4 | Root container in production | Medium | High | Add non-root USER in Dockerfile | **NEW** |
| R5 | Silent processing failures | Medium | Medium | Add per-reading error handling | **NEW** |
| R6 | `--hours 0.5` int truncation bug | Medium | Medium | Fix type to `float` | **NEW** |
| R7 | v2 data not reaching Center | Low | High | sync backlog=21, 401 Unauthorized on heartbeat | **EXISTING** |
| R8 | Breaking v1 during migration | Low | High | Phase 5 verified: v1 UNCHANGED | ↓ Reduced |

---

## 6. What's Working Well

1. **SA gate Phase 5**: v1 completely isolated from v2 — rollback dry-run verified
2. **Data pipeline**: Simulator → HTTP Poll → Processing → DuckDB, all 3 bugs fixed
3. **Docker packaging**: save/load workaround proven, `--network host` resolved connectivity
4. **Runbooks**: Migration + rollback both SA-aligned, Phases 4-6 properly marked BLOCKED
5. **VPS execution script**: Well-structured 6-phase design with `--skip-phases` CLI
6. **Config migration**: Handles 29 tags across 2 connectors correctly

---

## 7. Remaining Work Before Production Switch

| Priority | Task | Effort |
|---|---|---|
| **P0** | Move all credentials to env vars (4 files) | 1 session |
| **P0** | Add safety gate to `vps_execute_e2v2_7b.py` | 30 min |
| **P1** | Complete Phase 2 side-by-side comparison (now possible with data flowing) | 1 hour VPS |
| **P1** | Fix Center auth (heartbeat 401) so v2 syncs to Center | 1 session |
| **P1** | Runbook `--hours 0.5` bug fix | 15 min |
| **P2** | Add tests for 4 tools | 2 sessions |
| **P2** | Docker hardening (non-root, multi-stage, .dockerignore) | 1 session |
| **P3** | Populate dry-run results tables in runbooks | 30 min |

---

## 8. PM Recommendation

```text
🟡 CONDITIONAL PROCEED to next phase.

Edge v2 demonstrates core stability:
- 3/3 EV2-STAB gates passed
- Mirror mode verified (v1 unchanged)
- Data pipeline functional after bug fixes
- Docker packaging proven

However, SA should NOT approve production switch until:
1. All P0 issues resolved (credentials, safety gate)
2. Phase 2 side-by-side comparison shows equivalent data quality
3. Center auth fixed (v2 data must reach Center)
4. At minimum smoke tests added for migration tools

Recommendation: E2V2-8 (Production Readiness Hardening) before any switch decision.
```

---

## 9. SA Decision

```
[ ] APPROVED — Edge v2 ready for production switch
[ ] CONDITIONALLY APPROVED — Proceed to E2V2-8 hardening, resolve P0 before switch
[ ] NOT APPROVED — Issues to fix first

SA Notes:
```
