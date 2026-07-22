# Core Stabilization — Remediation Plan

> **Based on:** Baseline `ae8b611` | **Date:** 2026-07-22
> **Target Phase:** Phase 8 — Core Stabilization & Security Baseline

---

## Phase 8 Recommended Task Order

### Batch 1: Immediate Containment (P0 — must complete before any other work)

| Order | Task | ID | Effort |
|---|---|---|---|
| 1.1 | Fix hardcoded password in `main.py:237` → env var | SEC-001 | 2h |
| 1.2 | Fix 14 TypeScript errors (restore type imports + add annotations) | CQ-001,002,003 | 1h |
| 1.3 | Close public ports: 9998, 9999, 4840, 4841, 7000, 8002, 8100 | SEC-002, NET-001,002 | 30m |
| 1.4 | Verify `tsc` passes clean (blocked by 1.2) | — | 5m |

### Batch 2: Security Baseline (P1 — week 1)

| 2.1 | Generate random session_secret, move to env var | SEC-004 | 1h |
| 2.2 | Generate random API key, remove default from compose | SEC-005 | 30m |
| 2.3 | Add HTTPS via Let's Encrypt to nginx | SEC-003,006 | 4h |
| 2.4 | Route Edge v2 (8011) through nginx with TLS | SEC-006 | 2h |
| 2.5 | Align VPS repo to main commit | DRIFT-001 | 1h |
| 2.6 | Rebuild Edge v2 Docker image from HEAD | DRIFT-002 | 1h |
| 2.7 | Fix or remove EMQX | SEC-009 | 2h |

### Batch 3: Code Quality & Hardening (P2 — week 2)

| 3.1 | Add type imports for ThresholdConfig, AssetSignalConfig | CQ-001,002 | 30m |
| 3.2 | Add rate limiting to login endpoints | SEC-010 | 3h |
| 3.3 | Fix DOM XSS in nav.js (textContent or DOMPurify) | SEC-008 | 2h |
| 3.4 | Secure Edge user sync (TLS + audit log) | SEC-007 | 3h |
| 3.5 | Standardize Edge v2 config path | CQ-006 | 1h |
| 3.6 | Clean untracked temp files | CQ-004 | 15m |
| 3.7 | Handle TODO in modbus connector | CQ-005 | 2h |

### Batch 4: Reliability & Testing (P2 — week 3)

| 4.1 | Golden path integration test (Phase 8-01) | — | 8h |
| 4.2 | 24-hour soak test with failure injection | — | 24h |
| 4.3 | Backup/restore verification (PG + TDengine + Edge config) | — | 4h |
| 4.4 | Historian hardening (Phase 8-02) | — | 4h |

---

## GO/NO-GO Decision

```
Baseline status:          ESTABLISHED (ae8b611)
Immediate containment:    REQUIRED — SEC-001, SEC-002, CQ-001/002/003
Core Stabilization:       NO-GO (until Batch 1 complete)

Top 10 blocking findings:
  1. SEC-001 — Hardcoded password in source (CRITICAL)
  2. SEC-002 — 7 public ports exposed (CRITICAL)
  3. CQ-001 — ThresholdConfig type missing (MEDIUM — blocks build)
  4. CQ-002 — AssetSignalConfig type missing (MEDIUM — blocks build)
  5. CQ-003 — Implicit any types (MEDIUM — blocks build)
  6. SEC-003 — No HTTPS (HIGH)
  7. SEC-004 — Default session_secret (HIGH)
  8. SEC-005 — Default API key (HIGH)
  9. DRIFT-001 — VPS repo not traceable (HIGH)
  10. DRIFT-002 — Edge v2 image stale (HIGH)

Evidence still missing:
  - Backend clean build + test run
  - Edge v2 clean build from HEAD
  - Docker compose full up verification
  - RBAC test matrix execution
  - 24-hour soak test
  - Backup/restore verification
  - gitleaks/trufflehog/bandit/pip-audit automated scans
  - Golden path integration test

Recommended first remediation batch:
  1. Close public ports on VPS (SEC-002) — 30 min
  2. Fix TypeScript errors (CQ-001/002/003) — 1h  
  3. Move password to env var (SEC-001) — 2h
  → Then re-evaluate GO/NO-GO for full Phase 8
```

---

## Risk Acceptance

The following may require SA risk acceptance:

| Risk | Rationale |
|---|---|
| Password hashes in Edge sync API without TLS | Internal network only — accept if LAN is trusted |
| EMQX removed from architecture | Edge v2 doesn't use MQTT — no impact |
| No audit log | Can defer to Phase 9 |
| Hardcoded workspace IDs in UI | Not security-critical for single-tenant demo |
