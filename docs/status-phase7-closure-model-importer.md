# PlantOS Phase 7 Closure — Model Importer & Contract Governance

## 1. Phase 7 Objective

Phase 7 introduces a **governed model import capability** to PlantOS. It establishes the Integration Contract v2 as the single source of truth for industrial asset models, and provides a safe, phased pipeline to import those models into the PlantOS registry without breaking existing functionality.

## 2. Phase 7 Status

```
Status: ✅ FINAL CLOSURE
Phase 7.0: Model Importer — COMPLETE
Phase 7.1: SA Hardening — COMPLETE (all 6 conditions met)
Phase 7.2: SA Final Corrections — COMPLETE
ADR: docs/adr/ADR-0006-integration-contract-v2.md
Implemented: 2026-07-01
Final SA Approval: 2026-07-01
```

## 3. Phase 7.1 Hardening Results

| # | SA Condition | Status | Evidence |
|---|---|---|---|
| 1 | DB Migration: signals.status + plants.timezone | ✅ Done | `backend/app/db/migrations/add_status_timezone.py` |
| 2 | Seed script → Contract v2 support | ✅ Done | `backend/app/seed/vf_demo_plant.py` — detects v1/v2 |
| 3 | Apply Technical Report | ✅ Done | `docs/contracts/apply-technical-report.md` |
| 4 | Additional tests (5 new) | ✅ Done | `backend/tests/test_contracts_apply.py` — idempotency, hierarchy, orphan, smoke |
| 5 | Wording: "Operational Model Import Contract" | ✅ Done | 4 files updated (spec, ADR, schema, example) |
| 6 | Phase E blocked | ✅ Done | Noted in roadmap |

### Test Results (Phase 7.0 + 7.1)

| Test Category | Count | Passed |
|---|---|---|
| Validator tests (7-01) | 8 | ✅ 8/8 |
| Preview tests (7-02) | 3 | ✅ 3/3 |
| Apply basic tests (7-03) | 4 | ✅ 4/4 |
| **7.1 Idempotency** | 1 | ✅ |
| **7.1 Multi-level hierarchy** | 1 | ✅ |
| **7.1 Orphan report** | 1 | ✅ |
| **7.1 Smoke (50 signals)** | 1 | ✅ |
| **Total** | **19** | **✅ 19/19**

## 3. Deliverables Completed

### Documentation & Schema

- [x] `docs/contracts/plantos-integration-contract-spec.md` — Contract v2 specification (core/extensions separation, UNS policy, 18 validation rules, orphaned handling)
- [x] `schemas/plantos-integration-contract.schema.json` — Machine-readable JSON Schema for structural validation
- [x] `examples/contracts/vf-compressor-train.contract.yaml` — Example v2 contract (7 assets, 26 signals, OPC UA bindings, simulation behaviors)
- [x] `docs/adr/ADR-0006-integration-contract-v2.md` — Architecture decision record

### Backend Implementation

- [x] `backend/app/modules/contracts/__init__.py` — Module init
- [x] `backend/app/modules/contracts/schemas.py` — Pydantic models (ContractV2, 15 entity models)
- [x] `backend/app/modules/contracts/validator.py` — Cross-reference validator (18 rules + UNS path generator)
- [x] `backend/app/modules/contracts/preview.py` — Preview/diff logic (compare vs PostgreSQL)
- [x] `backend/app/modules/contracts/apply.py` — Safe apply logic (writes to DB via service layer)
- [x] `backend/app/modules/contracts/router.py` — 3 API endpoints
- [x] `backend/app/api/v1.py` — Router registration (MODIFIED: +1 line)

### API Endpoints

| Method | Endpoint | Phase | Status |
|---|---|---|---|
| POST | `/api/v1/contracts/validate` | B | ✅ Deployed |
| POST | `/api/v1/contracts/preview` | C | ✅ Deployed |
| POST | `/api/v1/contracts/apply` | D | ✅ Deployed |

### Tests

- [x] `backend/tests/test_contracts_validator.py` — 8 test cases (structure, references, uniqueness, formats)
- [x] `backend/tests/test_contracts_preview.py` — 3 test cases (new plant, existing plant, no-write)
- [x] `backend/tests/test_contracts_apply.py` — 4 test cases (new plant, conflict, mode check, skip)

### Coder Prompts

- [x] `docs/prompts/phase7-task01-contract-validator.md`
- [x] `docs/prompts/phase7-task02-contract-preview.md`
- [x] `docs/prompts/phase7-task03-contract-apply.md`

## 4. Architecture Decisions Locked

- [x] **Core vs Extensions separation**: Contract v2 separates core operational model (plant/area/asset/signal) from source-system extensions (bindings.opcua, simulation.behaviors, extensions.*)
- [x] **import_policy at API level**: Import behavior is controlled by the API caller, not embedded in the contract. Contract only provides `import_recommendation` as a hint.
- [x] **Phased pipeline**: Validate → Preview → Apply. Each phase builds on the previous. No phase proceeds without gate review.
- [x] **Safety defaults**: `on_conflict=fail`, `allow_update_existing=false`, `allow_delete_missing=false`, `orphaned_action=report`. Explicit opt-in required for any destructive action.
- [x] **UNS path generation**: Paths are generated algorithmically from contract entities, not manually specified.
- [x] **No VF coupling**: Core PlantOS CDM no longer depends on Virtual Factory-specific fields (`opcua_node_id`, `vf_internal_ref`, `vf_sensor_id`).
- [x] **Non-destructive validation**: Validate and Preview endpoints do not write to database. Only Apply writes, and only with explicit `mode: apply`.
- [x] **Orphaned entity handling**: Entities in DB but not in contract are reported as orphans. Default action: `report` (no changes). Supported future actions: `deactivate`, `delete`.

## 5. Test Results Summary

### Validator (7-01)

| Test | Result |
|---|---|
| Empty contract `{}` | 422 structure error ✅ |
| Valid minimal contract | `valid: true`, UNS paths generated ✅ |
| Invalid contract (4 errors) | All 4 caught: area plant_id, missing area, missing asset, signal_id format ✅ |
| Duplicate detection | asset_id, signal_id duplicates rejected ✅ |
| OPC UA NodeId format | Valid/invalid patterns detected ✅ |
| Missing bindings warning | Warning when system_type expects OPC UA ✅ |

### Preview (7-02)

| Test | Result |
|---|---|
| New plant (no DB data) | 4 creates, 0 conflicts ✅ |
| VF-DEMO (existing in DB) | 1 create, 3 conflicts, 26 orphans ✅ |
| Preview does not write | Second preview returns same result ✅ |

### Apply (7-03)

| Test | Result |
|---|---|
| New plant (APPLY-TEST-02) | 5 created (plant + area + asset + 2 signals) ✅ |
| Without `mode: apply` | Rejected with clear error ✅ |
| Empty `contract` wrapper | 422 validation error ✅ |
| Data lands in PostgreSQL | Verified plant appears in plants table ✅ |

## 6. Impact Assessment on Existing Modules

| Module | Impact | Status |
|---|---|---|
| **Asset API** | No changes | ✅ Unaffected |
| **Signal API** | No changes | ✅ Unaffected |
| **Measurement API** | No changes | ✅ Unaffected |
| **Edge Agent** | No changes | ✅ Unaffected |
| **Frontend UI** | No changes | ✅ Unaffected |
| **TDengine** | No access | ✅ Unaffected |
| **Seed script** | v1 contract still works | ✅ Backward compatible |
| **Database schema** | Additive: `status` on signals, `timezone` on plants | ✅ Migrated (Phase 7.1) |
| **API router** | +1 line in v1.py | ✅ Minimal |

## 7. Known Gaps & Future Work

### Phase 7 Remaining

| Item | Priority | Effort |
|---|---|---|
| **Phase E: Manifest Generation** — auto-generate Edge OPC UA manifest, simulator config, visualization bindings from contract | 🟢 P2 (blocked) | 3-4h |

### Phase 6 Backlog

| Item | Priority | Effort |
|---|---|---|
| **Token refresh** (sliding JWT expiration) | 🟡 P1 | 1h |
| **Timestamp → real UTC** (fix data pipeline) | 🟡 P1 | 2h |
| **VF systemd auto-start fix** | 🟡 P1 | 30min |

## 8. Architecture Compliance Check

| Constitution Law | Compliance |
|---|---|
| Law 1: No raw-data coupling | ✅ Contract separates bindings from core model |
| Law 2: No UI-to-database shortcut | ✅ Importer writes through service layer |
| Law 3: UNS as operational address space | ✅ UNS paths generated from contract entities |
| Law 4: CDM as application contract | ✅ Contract v2 is an Operational Model Import Contract aligned with PlantOS CDM |
| Law 5: Asset context mandatory | ✅ Signals always linked to assets |
| Law 6: Edge/Center separation | ✅ OPC UA bindings belong in extensions, not core |
| Law 7: Low-code governed | ✅ N/A — no low-code in this phase |

## 9. Solution Architect Review Checklist

- [x] Review ADR-0006 — Core/Extensions separation approved ✅
- [x] Review Contract v2 spec — Wording updated to "Operational Model Import Contract" ✅
- [x] Review JSON Schema — Sufficient for CI/CD ✅
- [x] Review API design — validate → preview → apply pipeline approved ✅
- [x] Review safety defaults — on_conflict=fail, no deletes approved ✅
- [x] Review import_policy location — API level approved ✅
- [x] Review orphaned handling — report default, deactivate future, delete guarded ✅
- [x] **SA Condition: DB Migration** — Completed ✅
- [x] **SA Condition: Seed script v2** — Completed ✅
- [x] **SA Condition: Technical Report** — Completed ✅
- [x] **SA Condition: Additional Tests** — 4 new tests, 19 total ✅
- [x] **SA Condition: Wording Fix** — Completed ✅
- [x] **SA Condition: Block Phase E** — Confirmed ✅
- [ ] **Final Approval** → Move to Phase 8

## 10. Approval

```
PM-Designer: ✅ Approved — Phase 7 final closure
Date: 2026-07-01

Solution Architect: ✅ Approved with minor corrections (applied)
Date: 2026-07-01
Notes: DB migration + seed v2 completed. CDM wording corrected.
Next: Phase 8 — Core Foundation Stabilization
```
