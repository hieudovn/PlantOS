# Task 8A-04 — PlantOS Apply WTP Contract

## Context

You are the Coder-Executioner for PlantOS Phase 8A.

Task 8A-03 is complete. Validate and Preview have passed:

```
Validate: valid=true, 0 errors, 107 warnings (all expected)
Preview:  149 creates (1 plant + 9 areas + 47 assets + 92 signals), 0 conflicts, 0 orphans
```

**PM Gate: APPROVED ✅ — Ready to apply.**

Your job: Apply the WTP contract to the PlantOS database on the VPS, verify the result, and create an apply report.

## ⚠️ WARNING

This is a **WRITE** operation. It modifies the PostgreSQL database. Double-check everything before running.

## Required Reading

```text
docs/reference-models/wtp-demo-01-design.md
docs/reference-models/wtp-demo-01-validation-report.md
backend/app/modules/contracts/apply.py          ← Understand apply logic
backend/tests/test_contracts_apply.py           ← Apply test patterns
```

## Implementation Checklist

### Step 1: Pre-Apply Safety Check

Before applying, snapshot the current DB state:

```bash
# Check VF-DEMO is intact
curl -s http://103.97.132.249:8000/api/v1/assets?plant_id=VF-DEMO \
  -H "X-API-Key: plantos-edge-key-2026" | python -c "import sys,json; d=json.load(sys.stdin); print(f'VF-DEMO assets: {len(d)}')"

# Check WTP-DEMO-01 does NOT exist yet
curl -s http://103.97.132.249:8000/api/v1/assets?plant_id=WTP-DEMO-01 \
  -H "X-API-Key: plantos-edge-key-2026" | python -c "import sys,json; d=json.load(sys.stdin); print(f'WTP-DEMO-01 assets: {len(d)}')"
```

Expected: VF-DEMO has 7 assets, WTP-DEMO-01 has 0 assets.

### Step 2: Apply

```bash
python -c "
import yaml, json, requests

with open('examples/contracts/wtp-demo-01.contract.yaml') as f:
    data = yaml.safe_load(f)

payload = {
    'contract': data,
    'import_policy': {
        'mode': 'apply',
        'on_conflict': 'fail',
        'allow_delete_missing': False,
        'orphaned_action': 'report'
    }
}

resp = requests.post(
    'http://103.97.132.249:8000/api/v1/contracts/apply',
    json=payload,
    headers={'X-API-Key': 'plantos-edge-key-2026'}
)
print(json.dumps(resp.json(), indent=2))
print(f'Status: {resp.status_code}')
"
```

### Step 3: Verify Apply Response

Expected response:

```json
{
  "plant_id": "WTP-DEMO-01",
  "mode": "apply",
  "results": {
    "plant": { "action": "created", "plant_id": "WTP-DEMO-01" },
    "areas_created": 9,
    "assets_created": 47,
    "signals_created": 92
  },
  "summary": {
    "total_created": 149,
    "total_updated": 0,
    "total_skipped": 0,
    "total_conflicts": 0
  },
  "orphaned": []
}
```

If `on_conflict: fail` and ANY entity already exists → 409 Conflict error. If this happens:
- Check if WTP-DEMO-01 was partially created earlier
- Consider using `on_conflict: skip` for retry
- Document the situation

### Step 4: Verify Database State

After successful apply, verify via GET endpoints:

```bash
# 4a. Verify plant
curl -s http://103.97.132.249:8000/api/v1/assets?plant_id=WTP-DEMO-01 \
  -H "X-API-Key: plantos-edge-key-2026" | python -c "
import sys, json
data = json.load(sys.stdin)
print(f'Total assets: {len(data)}')
types = {}
for a in data:
    t = a.get('asset_type', 'unknown')
    types[t] = types.get(t, 0) + 1
for t, c in sorted(types.items()):
    print(f'  {t}: {c}')
"
```

Expected: 47 assets across various types.

```bash
# 4b. Verify asset hierarchy (parent-child)
curl -s http://103.97.132.249:8000/api/v1/assets?plant_id=WTP-DEMO-01 \
  -H "X-API-Key: plantos-edge-key-2026" | python -c "
import sys, json
assets = json.load(sys.stdin)
roots = [a for a in assets if not a.get('parent_asset_id')]
children = [a for a in assets if a.get('parent_asset_id')]
print(f'Root assets: {len(roots)}')
print(f'Child assets: {len(children)}')
# Verify a few parent-child relationships
for a in assets:
    if a.get('asset_id') == 'SCREEN-101':
        print(f'SCREEN-101 parent: {a.get(\"parent_asset_id\")} (expected: INTAKE-STRUCTURE-101)')
    if a.get('asset_id') == 'RWP-101-MOTOR':
        print(f'RWP-101-MOTOR parent: {a.get(\"parent_asset_id\")} (expected: RWP-101)')
"
```

Expected: ~15-17 root assets, ~30-32 child assets. SCREEN-101 parent = INTAKE-STRUCTURE-101.

```bash
# 4c. Verify signals
curl -s "http://103.97.132.249:8000/api/v1/signals?plant_id=WTP-DEMO-01" \
  -H "X-API-Key: plantos-edge-key-2026" | python -c "
import sys, json
signals = json.load(sys.stdin)
print(f'Total signals: {len(signals)}')
"
```

Expected: 92 signals.

```bash
# 4d. Verify VF-DEMO still intact
curl -s http://103.97.132.249:8000/api/v1/assets?plant_id=VF-DEMO \
  -H "X-API-Key: plantos-edge-key-2026" | python -c "
import sys, json
data = json.load(sys.stdin)
print(f'VF-DEMO assets: {len(data)}')
"
```

Expected: Still 7 assets (unchanged).

### Step 5: Verify Quality Chain Signals Exist

```bash
curl -s "http://103.97.132.249:8000/api/v1/signals?plant_id=WTP-DEMO-01" \
  -H "X-API-Key: plantos-edge-key-2026" | python -c "
import sys, json
signals = json.load(sys.stdin)
# Key trend bundle signals
key_signals = [
    'RAW-WATER-QUALITY-STATION-101.raw_turbidity',
    'CLARIFIER-101.settled_turbidity',
    'FILTER-QUALITY-STATION-101.filtered_turbidity',
    'TRANSFER-OUTLET-QUALITY-STATION-101.outlet_turbidity',
    'DISINFECTION-QUALITY-STATION-101.free_chlorine',
    'TRANSFER-OUTLET-QUALITY-STATION-101.outlet_free_chlorine',
    'ENERGY-MONITORING-STATION-101.specific_energy_consumption',
    'PLANT-KPI-101.cost_per_m3',
    'QUALITY-TRACEABILITY-ENGINE-101.outlet_quality_risk_score',
]
signal_ids = {s['signal_id'] for s in signals}
for ks in key_signals:
    status = '✅' if ks in signal_ids else '❌ MISSING'
    print(f'{status} {ks}')
"
```

### Step 6: Create Apply Report

Create file:
```text
docs/reference-models/wtp-demo-01-apply-report.md
```

Template:

```markdown
# WTP-DEMO-01 Apply Report

## Date
YYYY-MM-DD

## Environment
- Host: 103.97.132.249:8000
- Backend version: 0.1.0
- Apply time: (ISO 8601 timestamp)

## Apply Parameters
| Parameter | Value |
|-----------|-------|
| Mode | apply |
| On conflict | fail |
| Allow delete | false |
| Orphaned action | report |

## Apply Results
| Entity | Created | Updated | Skipped | Conflicts |
|--------|---------|---------|---------|-----------|
| Plant | 1 | 0 | 0 | 0 |
| Areas | 9 | 0 | 0 | 0 |
| Assets | 47 | 0 | 0 | 0 |
| Signals | 92 | 0 | 0 | 0 |
| **Total** | **149** | **0** | **0** | **0** |

## Database Verification
| Check | Expected | Actual | Status |
|-------|----------|--------|--------|
| WTP-DEMO-01 assets | 47 | ? | ? |
| Root assets | ~15-17 | ? | ? |
| Child assets | ~30-32 | ? | ? |
| SCREEN-101 parent | INTAKE-STRUCTURE-101 | ? | ? |
| RWP-101-MOTOR parent | RWP-101 | ? | ? |
| Total signals | 92 | ? | ? |
| VF-DEMO intact | 7 assets | ? | ? |

## Key Signals Verified
| Signal | Present |
|--------|---------|
| RAW-WATER-QUALITY-STATION-101.raw_turbidity | ? |
| CLARIFIER-101.settled_turbidity | ? |
| FILTER-QUALITY-STATION-101.filtered_turbidity | ? |
| TRANSFER-OUTLET-QUALITY-STATION-101.outlet_turbidity | ? |
| PLANT-KPI-101.cost_per_m3 | ? |

## UNS Path Verification
(Spot-check 5-10 UNS paths against expected template)

## Issues
(List any issues or "None")

## Conclusion
- [ ] Apply successful, all entities created
- [ ] VF-DEMO unaffected
- [ ] Ready for Task 8A-05 (VF Simulator) and Task 8A-06 (Monitoring)
```

### Step 7: Rollback Plan (if needed)

If apply goes wrong:

```bash
# Option A: Delete WTP-DEMO-01 plant (cascading)
# (Only if supported by API — check with PM)
curl -X DELETE http://103.97.132.249:8000/api/v1/plants/WTP-DEMO-01 \
  -H "X-API-Key: plantos-edge-key-2026"

# Option B: Use on_conflict=skip for re-apply (idempotent)
# Change import_policy to {mode: apply, on_conflict: skip}
```

## Deliverables

1. `docs/reference-models/wtp-demo-01-apply-report.md` — Complete apply report with verified counts
2. Terminal output from all verification commands (pasted into report)

## Safety Gate

Do NOT proceed to Task 8A-05 or 8A-06 until:
- [ ] Apply returns 200 with expected counts
- [ ] All GET verifications pass
- [ ] VF-DEMO confirmed intact
- [ ] Key signals (quality chain) present
- [ ] Report filed and approved by PM
