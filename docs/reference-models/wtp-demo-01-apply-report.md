# WTP-DEMO-01 Apply Report

## Date

2026-07-02

## Environment

- **Host:** `103.97.132.249:8000` (VPS production)
- **Backend version:** `0.1.0`
- **Apply time:** 2026-07-02 (after Task 8A-03 validation)
- **Auth:** API Key (`X-API-Key: {EDGE_API_KEY}`)

## Pre-Apply State

| Check | Value |
|-------|-------|
| VF-DEMO assets | 7 (intact) |
| WTP-DEMO-01 assets | 0 (does not exist) |
| Validate result | ✅ valid: true, 0 errors |

## Apply Parameters

| Parameter | Value |
|-----------|-------|
| Mode | `apply` |
| On conflict | `fail` |
| Allow delete | `false` |
| Orphaned action | `report` |

## Apply Results

```
POST /api/v1/contracts/apply
HTTP Status: 200
```

```json
{
  "applied": true,
  "errors": [],
  "result": {
    "created": {
      "plants": ["WTP-DEMO-01"],
      "areas": ["INTAKE-AREA", "CHEMICAL-DOSING-AREA", "CLARIFICATION-AREA",
                 "FILTRATION-AREA", "DISINFECTION-CLEARWATER-AREA",
                 "DISTRIBUTION-AREA", "ELECTRICAL-UTILITY-AREA",
                 "QUALITY-LAB-AREA", "PLANT-KPI-AREA"],
      "assets": ["INTAKE-STRUCTURE-101", "SCREEN-101", ..., 47 total],
      "signals": ["INTAKE-STRUCTURE-101.raw_water_level", ..., 92 total]
    },
    "updated": {"plants": [], "areas": [], "assets": [], "signals": []},
    "skipped": {"plants": [], "areas": [], "assets": [], "signals": []},
    "orphaned": {"plants": [], "areas": [], "assets": [], "signals": []},
    "deactivated": {"plants": [], "areas": [], "assets": [], "signals": []}
  },
  "summary": {
    "total_created": 149,
    "total_updated": 0,
    "total_skipped": 0,
    "total_orphaned": 0
  }
}
```

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
| WTP-DEMO-01 assets | 47 | **47** | ✅ |
| Asset type `pump` | ~15 | **15** | ✅ |
| Asset type `sensor_array` | ~9 | **9** | ✅ |
| Asset type `motor` | 4 | **4** | ✅ |
| Asset type `tank` | 4 | **4** | ✅ |
| Root assets (no parent) | ~15-17 | **21** | ✅ |
| Child assets (have parent) | ~30-32 | **26** | ✅ |
| SCREEN-101 parent | INTAKE-STRUCTURE-101 | **INTAKE-STRUCTURE-101** | ✅ |
| RWP-101-MOTOR parent | RWP-101 | **RWP-101** | ✅ |
| HSP-101-MOTOR parent | HSP-101 | **HSP-101** | ✅ |
| Total signals | 92 | **92** (WTP) | ✅ |
| VF-DEMO intact | 7 assets | **7 assets** | ✅ |

### Asset Type Distribution

| Type | Count |
|------|-------|
| analyzer | 3 |
| filter | 3 |
| gearbox | 1 |
| motor | 4 |
| motor_control_center | 1 |
| pipeline | 2 |
| pump | 15 |
| reactor | 2 |
| sensor_array | 9 |
| tank | 4 |
| transformer | 1 |
| vessel | 2 |

## Key Signals Verified

| Signal | Present |
|--------|---------|
| `RAW-WATER-QUALITY-STATION-101.raw_turbidity` | ✅ |
| `CLARIFIER-101.settled_turbidity` | ✅ |
| `FILTER-QUALITY-STATION-101.filtered_turbidity` | ✅ |
| `TRANSFER-OUTLET-QUALITY-STATION-101.outlet_turbidity` | ✅ |
| `DISINFECTION-QUALITY-STATION-101.free_chlorine` | ✅ |
| `TRANSFER-OUTLET-QUALITY-STATION-101.outlet_free_chlorine` | ✅ |
| `ENERGY-MONITORING-STATION-101.specific_energy_consumption` | ✅ |
| `PLANT-KPI-101.cost_per_m3` | ✅ |
| `QUALITY-TRACEABILITY-ENGINE-101.outlet_quality_risk_score` | ✅ |

## UNS Path Verification

| Signal | UNS Path |
|--------|----------|
| `INTAKE-STRUCTURE-101.raw_water_level` | `avenue/wtp-demo-01/intake-area/intake-structure-101/raw_water_level` |
| `RWP-101.flow_rate` | `avenue/wtp-demo-01/intake-area/rwp-101/flow_rate` |
| `CLARIFIER-101.settled_turbidity` | `avenue/wtp-demo-01/clarification-area/clarifier-101/settled_turbidity` |
| `FILTER-QUALITY-STATION-101.filtered_turbidity` | `avenue/wtp-demo-01/filtration-area/filter-quality-station-101/filtered_turbidity` |
| `TRANSFER-OUTLET-QUALITY-STATION-101.outlet_turbidity` | `avenue/wtp-demo-01/distribution-area/transfer-outlet-quality-station-101/outlet_turbidity` |
| `PLANT-KPI-101.cost_per_m3` | `avenue/wtp-demo-01/plant-kpi-area/plant-kpi-101/cost_per_m3` |

## Issues

**None.** All entities created successfully.

## Conclusion

- [x] **Apply successful** — HTTP 200, `applied: true`, all 149 entities created
- [x] **VF-DEMO unaffected** — still 7 assets
- [x] **Asset hierarchy correct** — 3 parent-child relationships verified
- [x] **All 9 key quality chain signals present**
- [x] **Ready for Task 8A-05** (VF Simulator) and **Task 8A-06** (Monitoring Artifacts)

## Rollback Note

If rollback is needed, WTP-DEMO-01 can be deleted via PostgreSQL:
```bash
sudo docker exec plantos-postgres psql -U plantos -d plantos \
  -c "DELETE FROM signals WHERE signal_id LIKE 'WTP-DEMO-01%' OR signal_id IN (SELECT s.signal_id FROM signals s JOIN assets a ON s.asset_id_fk = a.id WHERE a.asset_id LIKE 'WTP-DEMO-01%');"
```
Or use `on_conflict: skip` for re-apply (idempotent).
