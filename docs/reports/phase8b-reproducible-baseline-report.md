# Phase 8B — Reproducible Baseline Report

> **Date:** 2026-07-22 | **Branch:** `stabilization/phase8` | **Commit:** `7936fb8`

---

## 1. Build Reproducibility Status

| Component | Build | Test | Status |
|---|---|---|---|
| Backend import | NOT_VERIFIED | NOT_VERIFIED | Windows env blocks venv |
| Backend tests | NOT_VERIFIED | NOT_VERIFIED | Need Linux env |
| Frontend tsc | NOT_VERIFIED | — | PowerShell blocks npm |
| Frontend vite build | NOT_VERIFIED | — | PowerShell blocks npm |
| Edge v2 pytest | NOT_VERIFIED | NOT_VERIFIED | Need Docker |
| Edge v2 docker build | NOT_VERIFIED | — | Need Docker |
| Docker compose | NOT_VERIFIED | — | Need compose |

**Root cause:** Windows development environment does not support clean build verification for Linux-targeted components.

---

## 2. Code Changes in Phase 8 Branch

| File | Change | Risk |
|---|---|---|
| `edge-v2/agent/main.py` | Hardcoded password → `EDGE_CENTER_PASSWORD` env var | Low — fail-fast if missing |
| `frontend/.../KeySignalsCard.tsx` | Added AssetSignalConfig import | Low |
| `frontend/.../AssetCard.tsx` | Added ThresholdConfig type alias | Low |
| `frontend/.../ConditionScoreCard.tsx` | Added ThresholdConfig type alias | Low |
| `frontend/.../ProcessBlock.tsx` | Added ThresholdConfig type alias | Low |
| `frontend/.../AssetConditionView.tsx` | Added explicit type annotations | Low |
| `frontend/.../useAssetSignals.ts` | Fixed data property access | Low |
| `frontend/.../TrendBundle.tsx` | Removed unsupported showLegend/showToolbox | Medium |
| `frontend/.../AssetBindings.tsx` | Fixed createBinding/deleteBinding args | Medium |
| `frontend/.../AssetForm.tsx` | Fixed getAreas args | Low |
| `frontend/.../KpiDefinitionsPage.tsx` | Fixed getKpis args | Low |

---

## 3. Remaining Gaps

| ID | Gap | Blocker |
|---|---|---|
| SEC-002 | 8 public ports | Needs VPS firewall changes |
| SEC-004 | Default session_secret | Needs Edge v2 image rebuild |
| SEC-005 | Default API key | Needs compose profile update |
| DRIFT-001 | VPS repo alignment | Needs VPS git reset |
| DRIFT-002 | Edge v2 image stale | Needs Docker build |
| SEC-009 | EMQX unhealthy | Needs fix or removal |
| D/G/H | Full build verification | Needs Linux environment |

---

## 4. Phase 8B Gate

```
Phase 8B reproducibility: NOT_PASS
  - Backend import from clean checkout: NOT_VERIFIED
  - Alembic empty DB upgrade: NOT_VERIFIED
  - Backend tests pass: NOT_VERIFIED
  - Edge tests pass: NOT_VERIFIED
  - Edge image builds from source: NOT_VERIFIED
  - Frontend npm run build passes: NOT_VERIFIED (14 errors fixed, build blocked)
  - Docker Compose clean deployment: NOT_VERIFIED
  - No hardcoded production credentials: PARTIAL (SEC-001 fixed, SEC-004/005 remain)
  - Old credentials rejected: NOT_VERIFIED
  - Services not externally reachable: NOT_CONTAINED
  - Runtime images traceable to commit SHA: NO
  - No docker cp required: NO (current state requires it)
  - Mandatory CI checks: NOT_IMPLEMENTED

Open Critical:  1 (SEC-002 network exposure not yet contained)
Open High:      5 (SEC-003,004,005, DRIFT-001,002)
Open Medium:    6 (SEC-007,008,010, CQ-001-003, CQ-006)

Runtime commit: 7936fb8 (stabilization/phase8)
Image digests:  NOT_BUILT
Remaining evidence: Backend build, Edge build, Compose deploy, CI workflow

GO/NO-GO for Phase 8C (Golden Path): NO-GO — reproducibility not established
GO/NO-GO for feature development: NO-GO — feature freeze remains
```

---

## 5. Recommended Next Step

Deploy `stabilization/phase8` to a clean Linux environment and run full build verification. All fixes are in source — verification is the only blocker.
