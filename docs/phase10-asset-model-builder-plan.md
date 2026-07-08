# PlantOS — Asset Model Builder: Implementation Plan

> **Author:** PM-Designer | **Date:** 2026-07-08  
> **Source:** SA Proposal "Asset Model Builder, Signal Binding, Calculation/KPI & Logic Governance"  
> **SA Status:** APPROVED with AST formula engine requirement  
> **Scope:** MVP 5 phase (AM-1 → AM-5), 2–3 tuần

---

## Executive Summary

Biến asset từ record tĩnh thành object vận hành có **template, attribute binding, calculated signal, KPI** và tích hợp với **Process View backend-driven**. MVP 5 phase, mỗi phase ~2-4 ngày, tổng ~12-17 ngày.

```
AM-1: Restore Semantic Core        (2-3 ngày)
AM-2: Asset Create/Edit UI          (2-3 ngày)
AM-3: Asset Template + Binding     (3-4 ngày)
AM-4: Formula/KPI Editor           (3-4 ngày)
AM-5: Process View Backend-Driven  (2-3 ngày)
─────────────────────────────────────────
                              TOTAL: ~12-17 ngày
```

---

## Architecture Decisions (SA Approved)

| # | Decision | Rationale |
|---|----------|-----------|
| 1 | **AST-based formula engine**, no `eval()` | Security: no arbitrary code execution. Audit trail. |
| 2 | **DB-first** templates, YAML export later | Iterate faster; Contract Registry later |
| 3 | **Hybrid** Process View: backend API + frontend fallback | Backward compat; gradual migration |
| 4 | Separate **calculated signal** vs **KPI** models, shared engine | Technical vs business distinction |
| 5 | **Current cache + optional historian** for results | Performance; not all KPIs need TDengine |
| 6 | **Cross-asset binding** allowed, same-plant validation | Needed for area/plant KPIs |
| 7 | **No visual rule builder** in MVP | Phase sau |

---

## Phase-by-Phase Plan

---

# Phase AM-1: Restore Semantic Core

> **Effort:** 2-3 ngày | **Depends on:** Nothing (P0 fix mostly done)

## Objective

Ensure `asset_role`, `signal_category`, `external_refs` are fully exposed in API responses, validated on input, and regression-tested.

## Current State

| Field | DB (migration 005) | ORM Model | API Schema | Status |
|-------|-------------------|-----------|------------|--------|
| `asset_role` | ✅ | ✅ (vừa fix P0) | ❌ Missing | **Fix** |
| `signal_category` | ✅ | ✅ (vừa fix P0) | ❌ Missing | **Fix** |
| `external_refs` | ✅ | ✅ (vừa fix P0) | ❌ Missing | **Fix** |

## Tasks

### Task 1: Add asset_role to Asset Schemas
**File:** `backend/app/modules/assets/schemas.py`

- `AssetCreate`: add `asset_role: str = Field("equipment", max_length=32)`
- `AssetUpdate`: add `asset_role: Optional[str] = Field(None, max_length=32)`
- `AssetResponse`: add `asset_role: str`
- Update `asset_service.py` -> `_asset_to_response()` to include `asset_role`

### Task 2: Add signal_category + external_refs to Signal Schemas
**File:** `backend/app/modules/signals/schemas.py`

- `SignalCreate`: add `signal_category: str = Field("measurement", max_length=32)`, add `external_refs: Optional[dict] = None`
- `SignalUpdate`: add `signal_category: Optional[str]`, add `external_refs: Optional[dict]`
- `SignalResponse`: add `signal_category: str`, add `external_refs: Optional[dict]`
- Update `signal_service.py` -> `_signal_to_response()` 

### Task 3: Update Contract Schema v2.0
**File:** `schemas/plantos-integration-contract.schema.json`

- Verify asset_role is in contract schema
- Verify signal_category is in contract schema
- If missing, add them

### Task 4: Regression Test
**File:** `backend/tests/test_regression_am1.py`

```python
def test_asset_response_has_asset_role():
    """AssetResponse must include asset_role"""
    ...

def test_signal_response_has_signal_category():
    """SignalResponse must include signal_category and external_refs"""
    ...

def test_process_view_asset_role_not_empty():
    """AreaMonitoringView must still show equipment assets after migration"""
    ...

def test_mes_event_contract_not_broken():
    """Runtime event builders must still resolve asset_role, signal_category"""
    ...
```

### Task 5: Frontend Update
- Update `AssetTable.tsx` to show asset_role column
- Update `AssetDetail.tsx` to show asset_role badge
- Verify `AssetCard.tsx` still works (it uses `asset.asset_role` from config — confirm API now provides it)

---

# Phase AM-2: Asset Create/Edit UI

> **Effort:** 2-3 ngày | **Depends on:** AM-1

## Objective

Complete asset CRUD in frontend — create/edit/delete forms with proper validation.

## Current State

- Backend: POST/PATCH/GET `/api/v1/assets` exist ✅
- Backend: No DELETE endpoint ❌
- Frontend: `AssetTable.tsx` lists assets, `AssetDetail.tsx` shows detail
- Frontend: No create/edit form ❌

## Backend Tasks

### Task 1: Add DELETE endpoint
**File:** `backend/app/modules/assets/router.py`

```python
@router.delete("/assets/{asset_id}", status_code=204)
def delete_asset(asset_id: str):
    """Soft-delete an asset (set lifecycle_status='deleted')."""
```

Also add to `AssetRepository`: `delete(asset_id)` method.

### Task 2: Add PATCH for areas
**File:** `backend/app/modules/assets/router.py`

```python
@router.patch("/areas/{area_id}", response_model=AreaResponse)
def update_area(area_id: str, data: AreaUpdate):
    """Update area metadata."""
```

### Task 3: Add validator for asset create/edit
**File:** `backend/app/modules/assets/validators.py` (NEW)

```python
def validate_asset_create(data: AssetCreate) -> list[str]:
    """Validate asset creation data. Returns list of error messages."""
    errors = []
    # area must exist
    # parent_asset must exist (if provided)
    # asset_id must be unique
    # asset_code must be unique (if provided)
    # asset_type must be in allowed vocabulary
    return errors
```

## Frontend Tasks

### Task 4: Asset Create/Edit Modal
**File:** `frontend/src/features/assets/AssetForm.tsx` (NEW)

- Modal with form fields matching `AssetCreate` schema
- Dropdown cho area_id (fetch từ API)
- Dropdown cho asset_type (hardcoded vocabulary list)
- Validation inline (required fields, unique ID)
- POST vs PATCH based on mode (create vs edit)

### Task 5: AssetTable Enhancements
**File:** `frontend/src/features/assets/AssetTable.tsx`

- Add "Create Asset" button → opens AssetForm modal
- Add edit icon per row → opens AssetForm modal in edit mode
- Add delete action (with confirmation dialog)
- Add asset_role column

### Task 6: Asset Vocabulary
**File:** `frontend/src/lib/vocabulary.ts` or `backend/app/core/vocabulary.py`

Define allowed values:
```python
ASSET_TYPES = ["pump", "filter", "tank", "motor", "sensor_array", "valve", "meter", "compressor_train", ...]
ASSET_ROLES = ["equipment", "functional_location", "subsystem", "component", "logical_group"]
```

---

# Phase AM-3: Asset Template + Binding

> **Effort:** 3-4 ngày | **Depends on:** AM-2

## Objective

Define asset templates with attributes, and bind real signals to asset attributes.

## Data Model (Migration 006)

```sql
-- asset_templates
CREATE TABLE asset_templates (
    template_id VARCHAR(64) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    asset_type VARCHAR(64) NOT NULL,
    asset_role VARCHAR(32) NOT NULL DEFAULT 'equipment',
    description TEXT,
    attributes_json JSONB NOT NULL DEFAULT '[]',
    domain_type VARCHAR(32) DEFAULT 'generic',
    metadata_json JSONB DEFAULT '{}',
    version INTEGER NOT NULL DEFAULT 1,
    status VARCHAR(32) NOT NULL DEFAULT 'draft',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- asset_attribute_bindings
CREATE TABLE asset_attribute_bindings (
    binding_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    asset_id VARCHAR(128) NOT NULL REFERENCES assets(asset_id),
    template_id VARCHAR(64) REFERENCES asset_templates(template_id),
    attribute_name VARCHAR(128) NOT NULL,
    signal_id VARCHAR(256) REFERENCES signals(signal_id),
    binding_type VARCHAR(32) NOT NULL DEFAULT 'direct',
    status VARCHAR(32) NOT NULL DEFAULT 'active',
    validation_status VARCHAR(32),
    validation_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(asset_id, attribute_name)
);
```

## Backend Tasks

### Task 1: Migration 006
**File:** `backend/migrations/versions/006_asset_templates.py`

Run `alembic revision --autogenerate -m "asset_templates"` after defining ORM models.

### Task 2: ORM Models
**Files:**
- `backend/app/modules/assets/models.py` — add `AssetTemplate`, `AssetAttributeBinding`
- Or create `backend/app/modules/asset_templates/models.py`

### Task 3: Template CRUD API
**File:** `backend/app/modules/asset_templates/router.py` (NEW)

```
POST   /api/v1/asset-templates              — create template
GET    /api/v1/asset-templates              — list all
GET    /api/v1/asset-templates/{id}         — get one
PATCH  /api/v1/asset-templates/{id}         — update
DELETE /api/v1/asset-templates/{id}         — delete
POST   /api/v1/asset-templates/seed         — seed default templates
```

### Task 4: Binding CRUD API
**File:** `backend/app/modules/asset_templates/router.py`

```
POST   /api/v1/assets/{asset_id}/bindings        — bind signal to attribute
GET    /api/v1/assets/{asset_id}/bindings        — list bindings
DELETE /api/v1/assets/{asset_id}/bindings/{id}   — unbind
POST   /api/v1/assets/{asset_id}/bindings/validate — validate all bindings
```

### Task 5: Seed Templates
**File:** `backend/app/seed/seed_templates.py` (NEW)

Create default templates:
- `pump_template_v1`: flow_rate (required), discharge_pressure (required), suction_pressure, motor_current, vibration, bearing_temperature
- `filter_template_v1`: filter_dp (required), effluent_flow (required), influent_turbidity
- `tank_template_v1`: level (required), inlet_flow, outlet_flow
- `motor_template_v1`: running_status (required), motor_current, speed
- `sensor_array_template_v1`: customizable

## Frontend Tasks

### Task 6: Asset Detail — Bindings Tab
**File:** `frontend/src/features/assets/AssetDetail.tsx`

Add tabs to AssetDetail:
- Overview (current)
- **Signals / Attributes** (NEW) — shows bindings table
- History (future)
- Configuration (future)

### Task 7: Bindings UI Component
**File:** `frontend/src/features/assets/AssetBindings.tsx` (NEW)

- Table: Attribute Name | Required | Bound Signal | Status | Actions
- "Bind Signal" button → search + select from existing signals
- "Create & Bind" → create new signal from attribute
- Validation indicators (red=missing required, yellow=unit mismatch, green=OK)

### Task 8: Template Selector in Asset Create
Update `AssetForm.tsx` — add Step 2: Select Template dropdown after choosing asset_type.

---

# Phase AM-4: Formula/KPI Editor

> **Effort:** 3-4 ngày | **Depends on:** AM-3

## Objective

Create safe formula engine for calculated signals and KPIs, with test/preview capability.

## Formula Engine Design

### AST-Based Safe Evaluator

```python
# backend/app/modules/formulas/engine.py

class SafeFormulaEngine:
    """AST-based safe expression evaluator.
    
    Allowed:
    - Numeric literals
    - Variable names (resolved from signal values)
    - Binary operators: + - * / ** %
    - Unary operators: + -
    - Comparison: > >= < <= == !=
    - Boolean: and or not
    - Function calls from registered whitelist
    - if(condition, true_val, false_val)
    
    Forbidden:
    - __import__, __builtins__
    - Attribute access, subscript
    - Lambda, comprehension, assignment
    - Loop, class/function definition
    """
    
    ALLOWED_FUNCTIONS = {
        'abs': abs, 'round': round,
        'min': min, 'max': max, 'sum': sum,
        'clamp': lambda x, lo, hi: max(lo, min(x, hi)),
        'normalize': lambda x, lo, hi: (x - lo) / (hi - lo) if hi != lo else 0,
        'if': lambda cond, a, b: a if cond else b,
    }
    
    def validate(self, formula: str, input_names: list[str]) -> list[str]:
        """Parse formula and return list of errors (empty = valid)."""
        ...
    
    def evaluate(self, formula: str, inputs: dict[str, float]) -> float:
        """Execute formula against input values. Raises FormulaError."""
        ...
```

### Backend Tasks

### Task 1: Formula Engine
**File:** `backend/app/modules/formulas/engine.py` (NEW)

Implement `SafeFormulaEngine` with:
- `validate(formula, input_names) → list[str]`
- `evaluate(formula, inputs) → float`
- Unit tests: `tests/test_formula_engine.py`

### Task 2: Calculated Signals Model + Migration (007 or 008)
**File:** `backend/migrations/versions/007_calculated_signals.py`

```sql
CREATE TABLE calculated_signals (
    calc_signal_id VARCHAR(128) PRIMARY KEY,
    asset_id VARCHAR(128) NOT NULL REFERENCES assets(asset_id),
    name VARCHAR(128) NOT NULL,
    display_name VARCHAR(255),
    formula TEXT NOT NULL,
    formula_meta_json JSONB DEFAULT '{}',
    inputs_json JSONB NOT NULL DEFAULT '[]',
    output_signal_id VARCHAR(256),
    output_unit VARCHAR(64),
    execution_mode VARCHAR(32) DEFAULT 'manual',
    schedule_interval INTEGER,
    status VARCHAR(32) DEFAULT 'draft',
    version INTEGER DEFAULT 1,
    last_run_at TIMESTAMPTZ,
    last_run_status VARCHAR(32),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

### Task 3: KPI Definitions Model + Migration
**File:** `backend/migrations/versions/008_kpi_definitions.py`

```sql
CREATE TABLE kpi_definitions (
    kpi_id VARCHAR(128) PRIMARY KEY,
    scope_type VARCHAR(32) NOT NULL,  -- plant, area, asset
    scope_id VARCHAR(128) NOT NULL,
    name VARCHAR(255) NOT NULL,
    display_name VARCHAR(255),
    description TEXT,
    kpi_category VARCHAR(32) DEFAULT 'operation',
    formula TEXT NOT NULL,
    formula_meta_json JSONB DEFAULT '{}',
    inputs_json JSONB NOT NULL DEFAULT '[]',
    unit VARCHAR(64),
    aggregation_window VARCHAR(32),
    target NUMERIC,
    warning_limit NUMERIC,
    critical_limit NUMERIC,
    display_priority INTEGER DEFAULT 0,
    show_in_process_view BOOLEAN DEFAULT false,
    status VARCHAR(32) DEFAULT 'draft',
    version INTEGER DEFAULT 1,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

### Task 4: Calculated Signal API
**File:** `backend/app/modules/formulas/router.py` (NEW)

```
POST   /api/v1/calculated-signals              — create
GET    /api/v1/calculated-signals              — list (filter by asset_id)
GET    /api/v1/calculated-signals/{id}         — get
PATCH  /api/v1/calculated-signals/{id}         — update
DELETE /api/v1/calculated-signals/{id}         — delete
POST   /api/v1/calculated-signals/{id}/test    — test with latest values
POST   /api/v1/calculated-signals/{id}/execute — run now
```

### Task 5: KPI API
**File:** `backend/app/modules/formulas/router.py`

```
POST   /api/v1/kpis                         — create
GET    /api/v1/kpis                         — list (filter: scope_type, scope_id)
GET    /api/v1/kpis/{id}                    — get
PATCH  /api/v1/kpis/{id}                    — update
DELETE /api/v1/kpis/{id}                    — delete
POST   /api/v1/kpis/{id}/test               — test with latest values
GET    /api/v1/kpis/current                 — get current values (filter: scope)
```

### Task 6: Formula Validation API
**File:** `backend/app/modules/formulas/router.py`

```
POST /api/v1/formulas/validate
Body: { "formula": "A + B * 2", "inputs": [{"name": "A", "signal_id": "X.y"}, ...]}
Response: { "valid": true/false, "errors": [...], "preview": 42.5 }
```

## Frontend Tasks

### Task 7: Formula Editor Component
**File:** `frontend/src/features/formulas/FormulaEditor.tsx` (NEW)

- Text input for formula
- Input variables selector (search signals, assign to A/B/C)
- "Test" button → calls `/api/v1/formulas/validate`
- Preview result
- Error display
- Save/Activate

### Task 8: Calculated Signals Page
**File:** `frontend/src/features/formulas/CalculatedSignalsPage.tsx` (NEW)

- List of calculated signals per asset
- Create/edit modal with formula editor
- Execute/test buttons

### Task 9: KPI Definition Page
**File:** `frontend/src/features/formulas/KpiDefinitionsPage.tsx` (NEW)

- List KPIs by scope (plant/area/asset)
- Create/edit with formula editor
- Target/warn/crit thresholds

---

# Phase AM-5: Process View Backend-Driven

> **Effort:** 2-3 ngày | **Depends on:** AM-3, AM-4

## Objective

Process View reads workflow, bindings, and KPI from backend API instead of frontend config files. Frontend config becomes fallback only.

## Backend Tasks

### Task 1: Process View API
**File:** `backend/app/modules/process_view/router.py` (NEW)

```
GET /api/v1/plants/{plant_id}/process-view
Response:
{
  "plant_id": "WTP-DEMO-01",
  "workflow": [
    {
      "id": "intake",
      "label": "Intake",
      "area_id": "INTAKE-AREA",
      "kpi_signal_id": "RWP-101.flow_rate",
      "kpi_unit": "m3/h"
    },
    ...
  ],
  "source": "backend"  // or "fallback"
}
```

**Note:** Initially, this API returns a HARDCODED config for WTP-DEMO-01 (migrated from `config/plants/wtp-demo-01.ts`). In future phases, it reads from DB template/binding/KPI tables.

### Task 2: Asset Condition Config API
**File:** `backend/app/modules/process_view/router.py`

```
GET /api/v1/assets/{asset_id}/condition-config
Response:
{
  "asset_id": "FILTER-101",
  "signals": [
    {"signal_id": "FILTER-101.filter_dp", "label": "DP", "unit": "kPa"},
    {"signal_id": "FILTER-101.effluent_flow", "label": "Effluent", "unit": "m3/h"}
  ],
  "thresholds": {
    "FILTER-101.filter_dp": {"warn": 60, "crit": 80, "direction": "high"}
  },
  "kpi_ids": [],
  "source": "backend"
}
```

### Task 3: Plant Workflow Config API
```
GET /api/v1/plants/{plant_id}/workflow-config
Response: { "blocks": [...], "source": "backend" }
```

## Frontend Tasks

### Task 4: API-Client Hook
**File:** `frontend/src/features/operations/hooks/useProcessConfig.ts` (NEW)

```ts
export function useProcessConfig(plantId: string) {
  return useQuery({
    queryKey: ["process-config", plantId],
    queryFn: () => fetchAPI(`/api/v1/plants/${plantId}/process-view`),
    staleTime: 60000,
    // Fallback to local config
    placeholderData: getPlantConfig(plantId),
  });
}
```

### Task 5: Update Components
- `PlantOverviewView.tsx` — use `useProcessConfig()` instead of `getWorkflowConfig()`
- `AreaMonitoringView.tsx` — use API bindings if available
- `AssetConditionView.tsx` — use API condition-config if available

### Task 6: Remove Hardcoded Configs (Optional — keep as fallback)
Keep `config/plants/wtp-demo-01.ts` and `config/index.ts` as fallback/seed data. The hook tries API first, falls back to local config.

---

## Cross-Cutting: AM-QA Regression Guardrail

Each phase MUST include:

| Phase | Regression Test |
|-------|----------------|
| AM-1 | AssetResponse/SignalResponse schema, Process View not broken |
| AM-2 | CRUD operations, validation errors returned correctly |
| AM-3 | Template seed works, binding validation catches errors |
| AM-4 | Formula safety (no eval), formula test returns correct result |
| AM-5 | Process View loads from API, fallback to local config if API fails |

**CI/CD:** Add `pytest tests/` to verify all regression tests pass before merge.

---

## Data Model Summary

```text
asset_templates                    -- template với attributes_json
asset_attribute_bindings           -- bind asset attribute → signal
calculated_signals                 -- formula → output signal
kpi_definitions                    -- business KPI
```

## API Summary (new endpoints)

```
AM-1: (none new — update existing schemas)
AM-2: DELETE /assets/{id}, PATCH /areas/{id}
AM-3: CRUD /asset-templates, CRUD /assets/{id}/bindings
AM-4: CRUD /calculated-signals, CRUD /kpis, POST /formulas/validate
AM-5: GET /plants/{id}/process-view, GET /assets/{id}/condition-config
```

## File Inventory (new files)

```
backend/
  app/modules/asset_templates/
    __init__.py, models.py, schemas.py, repository.py, router.py
  app/modules/formulas/
    __init__.py, engine.py, models.py, schemas.py, repository.py, router.py
  app/modules/process_view/
    __init__.py, router.py
  app/seed/seed_templates.py
  tests/test_formula_engine.py
  tests/test_regression_am1.py
  migrations/versions/006_asset_templates.py
  migrations/versions/007_calculated_signals.py
  migrations/versions/008_kpi_definitions.py

frontend/
  src/features/assets/
    AssetForm.tsx, AssetBindings.tsx
  src/features/formulas/
    FormulaEditor.tsx, CalculatedSignalsPage.tsx, KpiDefinitionsPage.tsx
  src/features/operations/hooks/
    useProcessConfig.ts
  src/lib/vocabulary.ts
```

---

## Risks & Open Questions

| # | Risk | Mitigation |
|---|------|------------|
| 1 | Backend container crash loses migrations (docker cp) | Run migration manually after deploy |
| 2 | Formula engine too complex for MVP | Use `simpleeval` library (locked down) if AST is too slow |
| 3 | Frontend form complexity | Use progressive disclosure — basic fields first, advanced later |
| 4 | Template attributes_json schema drift | Validate JSON against schema on write |
| 5 | Process View migration breaks demo | Keep fallback config — API failure = use local config |

---

## Next Actions

1. **PM writes coder prompts** for AM-1 (immediate) and AM-2 (after AM-1 done)
2. **Coder implements** AM-1 → AM-5 sequentially
3. **PM reviews** each phase output, runs regression tests
4. **Deploy** to VPS after each phase
