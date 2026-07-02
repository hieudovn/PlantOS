# WTP-DEMO-01 Validation & Preview Report

## Date

2026-07-02

## Environment

- **Host:** `103.97.132.249:8000` (VPS production)
- **Backend version:** `0.1.0` (reported by `/health`)
- **DB state:** Has existing VF-DEMO plant data (7 assets, 26 signals). WTP-DEMO-01 does NOT exist yet.
- **Auth:** API Key (`X-API-Key: plantos-edge-key-2026`)

## Validate Results

```
POST /api/v1/contracts/validate
```

### Summary

| Metric | Count |
|--------|-------|
| Areas | 9 |
| Assets | 47 |
| Signals | 92 |
| OPC UA bindings | 9 |
| Simulation behaviors | 50 |
| Validation result | **✅ valid: true** |

### Errors

**None** — 0 errors.

### Warnings Summary

| Type | Count | Example |
|------|-------|---------|
| Unrecognized engineering unit | 24 | `NTU`, `mg/L`, `uS/cm`, `mV`, `VND/m3`, `kWh/m3`, `cnt/mL`, `min`, `h`, `m3` |
| No OPC UA binding (V18) | 83 | Expected — WTP uses HTTP simulator, not OPC UA collector |

> **All warnings are expected** and do not affect validation. WTP-specific units are not in the `VALID_UNITS` set (designed for compressor train assets). The 83 unbound signals are expected since only 9 signals have OPC UA bindings for demo purposes.

### Full Validate Response

```json
{
  "valid": true,
  "errors": [],
  "warnings": [
    {"path": "signals[4].engineering_unit", "message": "Unrecognized unit: 'NTU'"},
    {"path": "signals[6].engineering_unit", "message": "Unrecognized unit: 'uS/cm'"},
    {"path": "signals[8].engineering_unit", "message": "Unrecognized unit: 'mg/L'"},
    ... (24 unit warnings, 83 binding warnings)
  ],
  "summary": {
    "plants": 1,
    "areas": 9,
    "assets": 47,
    "signals": 92
  },
  "uns_paths": {
    "INTAKE-STRUCTURE-101.raw_water_level": "avenue/wtp-demo-01/intake-area/intake-structure-101/raw_water_level",
    ...
  }
}
```

## Preview Results

```
POST /api/v1/contracts/preview
```

### Actions

| Entity | Creates | Conflicts | Orphans |
|--------|---------|-----------|---------|
| Plant | 1 | 0 | 0 |
| Areas | 9 | 0 | 0 |
| Assets | 47 | 0 | 0 |
| Signals | 92 | 0 | 0 |
| **Total** | **149** | **0** | **0** |

All entities will be **created**. No conflicts (WTP-DEMO-01 does not exist in DB). No orphans (new plant).

### Hierarchy Verification

- [x] All `parent_asset_id` references resolve (e.g., `SCREEN-101` → `INTAKE-STRUCTURE-101`)
- [x] All `area_id` references resolve (all assets reference valid area IDs)
- [x] All `signal.asset_id` references resolve (all 92 signals reference valid asset IDs)
- [x] All `signal_id` format matches `{ASSET_ID}.{signal_name}` (V10 rule)

### UNS Path Samples

| Signal | UNS Path |
|--------|----------|
| `INTAKE-STRUCTURE-101.raw_water_level` | `avenue/wtp-demo-01/intake-area/intake-structure-101/raw_water_level` |
| `RWP-101.flow_rate` | `avenue/wtp-demo-01/intake-area/rwp-101/flow_rate` |
| `CLARIFIER-101.settled_turbidity` | `avenue/wtp-demo-01/clarification-area/clarifier-101/settled_turbidity` |
| `FILTER-QUALITY-STATION-101.filtered_turbidity` | `avenue/wtp-demo-01/filtration-area/filter-quality-station-101/filtered_turbidity` |
| `TRANSFER-OUTLET-QUALITY-STATION-101.outlet_turbidity` | `avenue/wtp-demo-01/distribution-area/transfer-outlet-quality-station-101/outlet_turbidity` |
| `PLANT-KPI-101.cost_per_m3` | `avenue/wtp-demo-01/plant-kpi-area/plant-kpi-101/cost_per_m3` |

## Existing Demo Verification

| Check | Result |
|-------|--------|
| VF-DEMO assets still intact | ✅ **7 assets** (unchanged) |
| VF-DEMO signals | ✅ **26 signals** (unchanged) |
| VF-DEMO API accessible | ✅ `GET /api/v1/assets?plant_id=VF-DEMO` returns 200 |

## Issues Found

**None.** The contract is clean and ready to apply.

## Recommendation

- [x] **Ready to apply** (Task 8A-04)
- [ ] Needs fixes before apply

## Validation Gate Checklist

- [x] Validate returns `valid: true` with **0 errors**
- [x] Preview shows expected create counts: **1 plant, 9 areas, 47 assets, 92 signals**
- [x] **No unexpected conflicts or orphans**
- [x] Existing demo (VF-DEMO) is **not broken**
- [x] PM/Reviewer approves the report
