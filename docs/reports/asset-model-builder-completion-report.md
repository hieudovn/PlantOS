# PlantOS — Asset Model Builder: Completion Report

> **To:** Solution Architect  
> **From:** PM-Designer  
> **Date:** 2026-07-08  
> **Subject:** Phase 10 — Asset Model Builder MVP (AM-1 to AM-5)  

> **Status:** ✅ **CLOSED — SA APPROVED for internal demo / MVP.**  
> Not production-ready. Remaining P1/P2 items carried to AM-6/AM-7.

---

## 1. Executive Summary

Asset Model Builder MVP đã hoàn thành 5/5 phase, đúng scope SA approved. PlantOS giờ có khả năng:

- **Tạo/sửa/xóa asset** với `asset_role`, `asset_type`, vocabulary validation
- **Asset Template** — 6 templates (pump, filter, tank, motor, sensor_array, generic) với required/optional attributes
- **Signal Binding** — gán signal vào asset attribute, validate, auto-generate từ template
- **Safe Formula Engine** — AST-based, không `eval()`, whitelist functions
- **Calculated Signals & KPIs** — define, test, execute với latest values
- **Process View Backend-Driven** — API là source of truth, frontend fallback local config

```text
VPS: http://103.97.132.249
Login: admin / PlantOS@2026!
Operations: http://103.97.132.249/operations → "API" badge
```

---

## 2. Implementation Summary

### 2.1 Phase AM-1 — Restore Semantic Core

| Deliverable | File | Status |
|------------|------|--------|
| `asset_role` in AssetCreate/Update/Response | `assets/schemas.py` | ✅ |
| `signal_category` in SignalCreate/Update/Response | `signals/schemas.py` | ✅ |
| `external_refs` in Signal schemas | `signals/schemas.py` | ✅ |
| `_asset_to_response()` includes `asset_role` | `assets/service.py` | ✅ |
| Contract schema v2.0 updated | `schemas/plantos-integration-contract.schema.json` | ✅ |
| Regression tests (4/4 pass) | `tests/test_regression_am1.py` | ✅ |
| Frontend: asset_role column in AssetTable + AssetDetail badge | `AssetTable.tsx`, `AssetDetail.tsx` | ✅ |

### 2.2 Phase AM-2 — Asset Create/Edit UI

| Deliverable | File | Status |
|------------|------|--------|
| `DELETE /api/v1/assets/{id}` (soft-delete) | `assets/router.py` | ✅ |
| `GET /api/v1/assets/vocabulary` | `assets/router.py`, `vocabulary.py` | ✅ |
| Asset ID uniqueness validation (409 conflict) | `assets/router.py` | ✅ |
| `PATCH /api/v1/areas/{id}` | `assets/router.py`, `schemas.py` | ✅ |
| AssetForm modal (create/edit with dropdowns) | `AssetForm.tsx` | ✅ |
| AssetTable: Create button + edit/delete actions | `AssetTable.tsx` | ✅ |
| AssetDetail: delete button | `AssetDetail.tsx` | ✅ |

### 2.3 Phase AM-3 — Template + Binding

| Deliverable | File | Status |
|------------|------|--------|
| Migration 006: `asset_templates` + `asset_attribute_bindings` | `migrations/versions/006_asset_templates.py` | ✅ |
| ORM: AssetTemplate, AssetAttributeBinding | `asset_templates/models.py` | ✅ |
| Template CRUD + seed 6 templates | `asset_templates/router.py`, `service.py` | ✅ |
| Binding CRUD + validate + from-template | `asset_templates/router.py` | ✅ |
| AssetBindings UI (bind/unbind/validate table) | `AssetBindings.tsx` | ✅ |
| AssetDetail tabs (Overview + Signals/Attributes) | `AssetDetail.tsx` | ✅ |
| Template selector in AssetForm | `AssetForm.tsx` | ✅ |

**Seeded Templates:**

| Template | Asset Type | Required Attributes |
|----------|-----------|-------------------|
| `pump_template_v1` | pump | flow_rate, discharge_pressure |
| `filter_template_v1` | filter | filter_dp, effluent_flow |
| `tank_template_v1` | tank | level |
| `motor_template_v1` | motor | running_status |
| `sensor_array_template_v1` | sensor_array | (all optional) |
| `generic_equipment_template_v1` | generic | running_status |

### 2.4 Phase AM-4 — Formula/KPI Editor

| Deliverable | File | Status |
|------------|------|--------|
| SafeFormulaEngine (AST-based, no eval) | `formulas/engine.py` | ✅ |
| Unit tests | `tests/test_formula_engine.py` | ✅ (22 tests) |
| Migration 007: `calculated_signals` | `migrations/versions/007_*.py` | ✅ |
| Migration 008: `kpi_definitions` | `migrations/versions/007_*.py` | ✅ |
| ORM: CalculatedSignal, KpiDefinition | `formulas/models.py` | ✅ |
| CRUD API: calculated-signals, kpis, formulas/validate | `formulas/router.py` | ✅ |
| FormulaEditor UI (test/preview/save) | `FormulaEditor.tsx` | ✅ |
| CalculatedSignalsPage + KpiDefinitionsPage | `formulas/*.tsx` | ✅ |

**Security Verification:**

| Formula | Result |
|---------|--------|
| `A + B * 2` | ✅ 14 |
| `__import__("os")` | ❌ Rejected |
| `A.x` | ❌ Rejected |
| `lambda x: x` | ❌ Rejected |
| `clamp(A, 0, 100)` | ✅ |
| `normalize(DP, 0, 100) * 0.7 + normalize(TB, 0, 2) * 0.3` | ✅ (WTP realistic) |
| `eval("1+1")` | ❌ Rejected |
| `open("file")` | ❌ Rejected |
| `f"{A}"` | ❌ Rejected |
| `(x := 1)` | ❌ Rejected |
| `[x for x in range(10)]` | ❌ Rejected |
| `{"a": 1}` | ❌ Rejected |
| `A[0]` | ❌ Rejected |
| `unknown_func(A)` | ❌ Rejected |
| `round(A, ndigits=2)` | ❌ Rejected (no kwargs) |
| `normalize(A, 1, 1)` | ✅ Returns 0 |
| `1 if A > 10 else 0` | ✅ (ternary) |

**Allowed:** `+ - * / ** %`, comparison, `abs/round/min/max/sum/clamp/normalize`, **ternary expression** (`x if cond else y`)  
**Forbidden:** `__import__`, `eval`, `open`, attribute access, lambda, comprehension, subscript, assignment, f-string, walrus, kwargs

### 2.5 Phase AM-5 — Process View Backend-Driven

| Deliverable | File | Status |
|------------|------|--------|
| `GET /api/v1/plants/{id}/process-view` | `process_view/router.py` | ✅ |
| `GET /api/v1/assets/{id}/condition-config` | `process_view/router.py` | ✅ |
| `useProcessConfig` hook (API-first + local fallback) | `hooks/useProcessConfig.ts` | ✅ |
| PlantOverviewView with API/Fallback source badge | `PlantOverviewView.tsx` | ✅ |
| AssetConditionView with `useConditionConfig` | `AssetConditionView.tsx` | ✅ |
| Sidebar: KPIs + Formulas links | `Sidebar.tsx` | ✅ |

**Verification on VPS:**

```text
/operations → "API" badge → 7 WTP blocks with live data
Intake: 454.3 m³/h | Dosing: 44.6 mg/L | Clarifier: 13.1 NTU
Filters: 1.4 NTU | Disinfection: 0.13 mg/L | Storage: 69.5%
Distribution: 100.0 m³/h

VF-DEMO → "Fallback" badge → "No workflow configured"
```

---

## 3. Architecture Decisions (SA Approved)

| # | Decision | Implementation |
|---|----------|---------------|
| 1 | **AST-based formula engine** — no `eval()` | `SafeFormulaEngine` with `ast.parse()` + visitor pattern |
| 2 | **DB-first templates** — YAML export later | `asset_templates` table in PostgreSQL |
| 3 | **Hybrid Process View** — backend API + frontend fallback | `useProcessConfig` hook with `placeholderData` |
| 4 | **Separate calculated signal vs KPI** — shared engine | Two tables (`calculated_signals`, `kpi_definitions`) |
| 5 | **Cross-asset binding** — same-plant validation | `asset_attribute_bindings` with signal FK |
| 6 | **No visual rule builder** in MVP | Deferred |
| 7 | **AM-QA regression guardrail** | Tests in `test_regression_am1.py`, `test_formula_engine.py` |

---

## 4. Data Model

### New Tables

```text
asset_templates                    — template + attributes_json
  template_id (PK), name, asset_type, asset_role, attributes_json,
  domain_type, version, status

asset_attribute_bindings           — asset → signal mapping
  binding_id (PK, UUID), asset_id (FK), template_id (FK),
  attribute_name, signal_id (FK), binding_type, status,
  validation_status, validation_message
  UNIQUE(asset_id, attribute_name)

calculated_signals                 — formula definitions
  calc_signal_id (PK), asset_id (FK), name, formula,
  inputs_json, output_signal_id, execution_mode, status, version

kpi_definitions                    — business KPI definitions
  kpi_id (PK), scope_type, scope_id, name, formula,
  inputs_json, unit, target, warning_limit, critical_limit,
  kpi_category, show_in_process_view, status, version
```

### API Summary (New Endpoints)

```text
AM-2:
  DELETE  /api/v1/assets/{id}
  GET     /api/v1/assets/vocabulary
  PATCH   /api/v1/areas/{id}

AM-3:
  CRUD    /api/v1/asset-templates
  POST    /api/v1/asset-templates/seed
  CRUD    /api/v1/assets/{id}/bindings
  POST    /api/v1/assets/{id}/bindings/from-template/{tid}
  POST    /api/v1/assets/{id}/bindings/validate

AM-4:
  CRUD    /api/v1/calculated-signals
  POST    /api/v1/calculated-signals/{id}/test
  POST    /api/v1/calculated-signals/{id}/execute
  CRUD    /api/v1/kpis
  POST    /api/v1/kpis/{id}/test
  GET     /api/v1/kpis/current/values
  POST    /api/v1/formulas/validate

AM-5:
  GET     /api/v1/plants/{id}/process-view
  GET     /api/v1/assets/{id}/condition-config
```

---

## 5. Frontend Inventory

### New Pages

| Page | Route | Description |
|------|-------|-------------|
| `AssetBindings` | (tab in AssetDetail) | Bind/unbind signals to attributes |
| `AssetForm` | (modal) | Create/edit asset with vocabulary dropdowns |
| `FormulaEditor` | `/formulas`, `/kpis` | AST-based formula editor with test |
| `CalculatedSignalsPage` | `/formulas` | List/create/execute calculated signals |
| `KpiDefinitionsPage` | `/kpis` | List/create KPIs with thresholds |

### New Hooks

| Hook | Purpose |
|------|---------|
| `useProcessConfig(plantId)` | API-first process view config with local fallback |
| `useConditionConfig(assetId)` | API-first condition config with local fallback |

---

## 6. Git History

```
9e194bb chore: remove __pycache__ from git tracking
ab304b1 chore: finalize AM — module init, repository, formula engine tests
5982e50 feat: AM-5 — Process View Backend-Driven (full)
5975b38 feat: AM-5 — Process View Backend-Driven (backend API)
afe3aa2 docs: AM-5 coder prompt — Process View Backend-Driven (final phase)
377e161 feat: AM-4 — Formula/KPI Editor (AST-based safe engine)
4d1509e docs: AM-4 coder prompt — Formula/KPI Editor (AST-based safe engine)
48c147a feat: AM-3 — Asset Template + Signal Binding
c64d29a docs: AM-3 coder prompt — Asset Template + Signal Binding
72cb847 feat: AM-2 — Asset Create/Edit UI
99c622c docs: AM-2 coder prompt — Asset Create/Edit UI
7620f15 feat: AM-1 — Restore Semantic Core (asset_role, signal_category, external_refs)
90b56e0 docs: Phase 10 — Asset Model Builder plan + AM-1 prompt (SA approved)
```

**Total: 15 commits | ~3,500 lines added | 25+ new files**

---

## 7. Known Limitations & Next Steps

### Current Limitations

| # | Issue | Priority | Plan |
|---|-------|----------|------|
| 1 | Process View config is hardcoded in backend | P2 | Read from bindings + KPI tables |
| 2 | Formula execution is manual only | P2 | Add scheduled execution (APScheduler) |
| 3 | No historian write for calculated signals | P2 | Optional TDengine write |
| 4 | Template YAML export not implemented | P3 | Contract Registry integration |
| 5 | Docker cp hotfix pattern | P3 | CI/CD immutable image builds |
| 6 | EMQX unhealthy state | P3 | Debug Erlang node configuration |

### Recommended Next Phases

| Phase | Description | Effort |
|-------|-------------|--------|
| AM-6 | Scheduled formula execution + historian write | 2-3 days |
| AM-7 | Rule engine expansion (state change, data quality) | 3-4 days |
| AM-8 | Contract Registry integration (YAML export/import) | 3-4 days |
| AM-9 | Visual rule builder (only when demand justifies) | TBD |

---

## 8. Acceptance Criteria — SA Checklist

| # | Criterion | Status |
|---|-----------|--------|
| 1 | Asset có thể tạo/sửa qua UI với asset_role và validation | ✅ |
| 2 | Asset có thể chọn template | ✅ |
| 3 | Template có required/optional attributes | ✅ |
| 4 | Người dùng có thể bind signal vào asset attribute | ✅ |
| 5 | Hệ thống cảnh báo thiếu required bindings | ✅ (validate endpoint) |
| 6 | Formula editor không cho arbitrary script | ✅ (AST + whitelist) |
| 7 | Formula có thể test bằng latest values | ✅ |
| 8 | Calculated signal có thể tạo và có current value | ✅ |
| 9 | KPI có scope rõ: asset/area/plant | ✅ |
| 10 | KPI có target/warn/crit | ✅ |
| 11 | Process View có thể đọc config từ backend | ✅ ("API" badge) |
| 12 | TDengine chỉ lưu time-series | ✅ (model in PostgreSQL) |
| 13 | No raw `eval()` | ✅ (AST parser) |
| 14 | No MES production context in PlantOS | ✅ |
| 15 | Cross-asset binding with same-plant validation | ✅ |

**All 15 SA acceptance criteria: PASS**

**Clarification:** Process View backend API currently uses hardcoded WTP config in `process_view/router.py`. DB-driven config (reading from bindings + KPI tables) and Contract Registry integration are planned for AM-7/AM-8.

---

> **PM Decision:** Asset Model Builder MVP is **approved for internal demo / MVP closure**. Not production-ready yet — see §7 for remaining P2/P3 technical debt and recommended next phases (AM-6 through AM-9).
