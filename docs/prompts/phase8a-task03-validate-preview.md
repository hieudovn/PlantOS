# Task 8A-03 — PlantOS Validate & Preview WTP Contract

## Context

You are the Coder-Executioner for PlantOS Phase 8A.

Task 8A-02 is complete. The WTP contract file is ready at:
```text
examples/contracts/wtp-demo-01.contract.yaml
```

Local validation passed: **0 errors, 107 warnings** (all warnings expected — WTP-specific units + no OPC UA bindings).

Your job: Run the contract through the PlantOS **validate** and **preview** API endpoints on the running PlantOS instance (VPS or local), and produce a validation report.

## Required Reading

```text
docs/reference-models/wtp-demo-01-design.md                    ← Design doc
docs/contracts/plantos-integration-contract-spec.md             ← Contract spec
backend/app/modules/contracts/validator.py                      ← Validation rules
backend/tests/test_contracts_validator.py                       ← Validator tests
backend/tests/test_contracts_preview.py                         ← Preview tests
```

## Prerequisites

- PlantOS backend must be running (VPS or localhost:8000)
- Database must be accessible (PostgreSQL)
- If WTP-DEMO-01 already exists in DB from a previous attempt, note it

## Implementation Checklist

### Step 1: Validate

```bash
curl -s -X POST http://<HOST>:8000/api/v1/contracts/validate \
  -H "Content-Type: application/json" \
  -d @examples/contracts/wtp-demo-01.contract.yaml | python -m json.tool
```

Or if curl can't read YAML directly, convert first:

```bash
python -c "
import yaml, json, requests
with open('examples/contracts/wtp-demo-01.contract.yaml') as f:
    data = yaml.safe_load(f)
resp = requests.post('http://<HOST>:8000/api/v1/contracts/validate', json=data)
print(json.dumps(resp.json(), indent=2))
"
```

### Step 2: Check Validate Response

The response should contain:

```json
{
  "valid": true,
  "contract_version": "2.0",
  "plant_id": "WTP-DEMO-01",
  "summary": {
    "areas": 9,
    "assets": 47,
    "signals": 92,
    "opcua_bindings": 9
  },
  "errors": [],
  "warnings": [...]
}
```

Expected:
- `valid: true`
- `errors: []`
- Warnings for unrecognized units (NTU, mg/L, etc.) and unbound signals — these are OK

If validation fails with errors:
1. Document each error
2. Check if it's a real issue or data format problem
3. Fix if trivial, report if needs PM review

### Step 3: Preview

```bash
python -c "
import yaml, json, requests
with open('examples/contracts/wtp-demo-01.contract.yaml') as f:
    data = yaml.safe_load(f)

payload = {
    'contract': data,
    'import_policy': {
        'mode': 'preview',
        'on_conflict': 'fail'
    }
}
resp = requests.post('http://<HOST>:8000/api/v1/contracts/preview', json=payload)
print(json.dumps(resp.json(), indent=2))
"
```

### Step 4: Analyze Preview Response

Expected response shape:

```json
{
  "plant_id": "WTP-DEMO-01",
  "mode": "preview",
  "results": {
    "plant": { "action": "create", ... },
    "areas": [
      { "area_id": "INTAKE-AREA", "action": "create" },
      ...
    ],
    "assets": [
      { "asset_id": "INTAKE-STRUCTURE-101", "action": "create" },
      ...
    ],
    "signals": [
      { "signal_id": "INTAKE-STRUCTURE-101.raw_water_level", "action": "create" },
      ...
    ]
  },
  "orphaned": [],
  "conflicts": []
}
```

Verify:
- `plant.action = "create"` (assuming clean DB)
- All 9 areas → "create"
- All 47 assets → "create"
- All 92 signals → "create"
- `orphaned: []`
- `conflicts: []`

### Step 5: Handle Edge Cases

| Scenario | Action |
|----------|--------|
| WTP-DEMO-01 already exists in DB | Document conflicts. If previous test data, suggest clearing DB or using `on_conflict: skip` |
| Preview shows orphans | Document them. Should be empty for new plant |
| API returns 422 | Check payload format. May need to wrap contract differently |
| API returns 500 | Check backend logs, report error |
| VPS unreachable | Test against localhost:8000 instead |

### Step 6: Create Validation Report

Create file:
```text
docs/reference-models/wtp-demo-01-validation-report.md
```

Report must include:

```markdown
# WTP-DEMO-01 Validation & Preview Report

## Date
YYYY-MM-DD

## Environment
- Host: <HOST>:8000
- Backend version: (check /health)
- DB state: (clean / has existing data)

## Validate Results

### Summary
| Metric | Count |
|--------|-------|
| Areas | 9 |
| Assets | 47 |
| Signals | 92 |
| OPC UA bindings | 9 |
| Simulation behaviors | 50 |

### Errors
(List all errors, or "None")

### Warnings Summary
| Type | Count | Example |
|------|-------|---------|
| Unrecognized unit | 24 | NTU, mg/L, VND/m3 |
| No OPC UA binding | 83 | (expected for HTTP simulator) |

## Preview Results

### Actions
| Entity | Creates | Updates | Conflicts | Orphans |
|--------|---------|---------|-----------|---------|
| Plant | 1 | 0 | 0 | 0 |
| Areas | 9 | 0 | 0 | 0 |
| Assets | 47 | 0 | 0 | 0 |
| Signals | 92 | 0 | 0 | 0 |

### Hierarchy Verification
- [ ] All parent_asset_id references resolve
- [ ] All area_id references resolve
- [ ] All signal.asset_id references resolve

### UNS Path Sample
| Signal | UNS Path |
|--------|----------|
| INTAKE-STRUCTURE-101.raw_water_level | avenue/wtp-demo-01/intake-area/intake-structure-101/raw_water_level |
| TRANSFER-OUTLET-QUALITY-STATION-101.outlet_turbidity | avenue/wtp-demo-01/distribution-area/transfer-outlet-quality-station-101/outlet_turbidity |
| PLANT-KPI-101.cost_per_m3 | avenue/wtp-demo-01/plant-kpi-area/plant-kpi-101/cost_per_m3 |

## Issues Found
(List any issues or "None")

## Recommendation
- [ ] Ready to apply
- [ ] Needs fixes before apply (list fixes)
```

### Step 7: Verify No Existing Demo Broken

```bash
curl -s http://<HOST>:8000/api/v1/assets?plant_id=VF-DEMO | python -m json.tool | head -20
```

Verify VF-DEMO assets are intact. Count should match pre-existing state.

## Deliverables

1. `docs/reference-models/wtp-demo-01-validation-report.md` — Complete validation report
2. Terminal output showing validate + preview API responses (pasted into report)

## Validation Gate

Do NOT proceed to Task 8A-04 (Apply) until:
- [ ] Validate returns `valid: true` with 0 errors
- [ ] Preview shows expected create counts
- [ ] No unexpected conflicts or orphans
- [ ] Existing demo (VF-DEMO) is not broken
- [ ] PM/Reviewer approves the report

## Reference: API Payload Format

The `/api/v1/contracts/preview` endpoint expects:

```json
{
  "contract": { ... full contract YAML as JSON ... },
  "import_policy": {
    "mode": "preview",
    "on_conflict": "fail"
  }
}
```

The `/api/v1/contracts/apply` endpoint expects the same shape with `mode: "apply"`.

Note: `import_policy` is required in the request body. The contract file's `import_recommendation` is only a hint.
