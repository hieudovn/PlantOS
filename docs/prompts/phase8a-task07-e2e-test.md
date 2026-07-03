# Task 8A-07 — WTP-DEMO-01 End-to-End Demo Test

## Context

You are the Coder-Executioner for PlantOS Phase 8A.

All previous tasks are complete:
- 8A-02: Contract file ✅
- 8A-04: Applied (149 entities) ✅
- 8A-05: Ingestion running, OPC UA fixed ✅
- VF: WTP simulator running, HTTP ingest active, 8 scenarios available ✅
- 8A-06: Monitoring artifacts created ✅

Your job: Run the final E2E demo scenarios to prove the full PlantOS pipeline works:
```
Contract → Registry → Simulator → Ingestion → Historian → Query → Visualization
```

## Environment

| Component | Endpoint |
|-----------|----------|
| PlantOS API | `http://103.97.132.249:8000` |
| VF Scenario API | `http://103.97.132.249:8100` |
| API Key | `X-API-Key: {EDGE_API_KEY}` |

---

## Part A: Verify Baseline (Normal Operation)

### A1: Confirm current scenario

```bash
curl -s http://103.97.132.249:8100/api/v1/scenarios/current | python -m json.tool
```

Ensure: `normal_operation`

### A2: Query turbidity chain (current + trend)

```bash
# Current values
for sid in \
  RAW-WATER-QUALITY-STATION-101.raw_turbidity \
  CLARIFIER-101.settled_turbidity \
  FILTER-QUALITY-STATION-101.filtered_turbidity \
  TRANSFER-OUTLET-QUALITY-STATION-101.outlet_turbidity
do
  curl -s "http://103.97.132.249:8000/api/v1/signals/$sid/current" \
    -H "X-API-Key: {EDGE_API_KEY}" | python -c "import sys,json; d=json.load(sys.stdin); print(f'{d[\"signal_id\"]}: {d[\"value\"]}')" 2>/dev/null
done
```

### A3: Verify treatment relationship

Normal operation should show:
- `raw_turbidity`: 30-60 NTU (highest)
- `settled_turbidity`: 5-12 NTU (~15-20% of raw)
- `filtered_turbidity`: 0.1-0.5 NTU (very low)
- `outlet_turbidity`: 0.1-0.5 NTU (similar to filtered)

### A4: Query cost KPIs

```bash
for sid in \
  ENERGY-MONITORING-STATION-101.specific_energy_consumption \
  CHEMICAL-CONSUMPTION-STATION-101.chemical_cost_per_m3 \
  PLANT-KPI-101.cost_per_m3
do
  curl -s "http://103.97.132.249:8000/api/v1/signals/$sid/current" \
    -H "X-API-Key: {EDGE_API_KEY}" | python -c "import sys,json; d=json.load(sys.stdin); print(f'{d[\"signal_id\"]}: {d[\"value\"]}')" 2>/dev/null
done
```

### A5: Verify traceability signals

```bash
for sid in \
  QUALITY-TRACEABILITY-ENGINE-101.outlet_quality_risk_score \
  QUALITY-TRACEABILITY-ENGINE-101.probable_root_cause_code
do
  curl -s "http://103.97.132.249:8000/api/v1/signals/$sid/current" \
    -H "X-API-Key: {EDGE_API_KEY}" | python -c "import sys,json; d=json.load(sys.stdin); print(f'{d[\"signal_id\"]}: {d[\"value\"]}')" 2>/dev/null
done
```

Normal: `outlet_quality_risk_score` should be low (0-3), `probable_root_cause_code` = 0.

---

## Part B: Scenario Tests

### Scenario 1: Raw Water Contamination

```bash
# 1. Switch scenario
curl -s -X POST http://103.97.132.249:8100/api/v1/scenarios/raw_water_contamination

# 2. Wait 30s for transition
sleep 35

# 3. Verify: raw_turbidity spike, outlet risk rises, traceability fires
echo "=== After raw_water_contamination ==="
for sid in \
  RAW-WATER-QUALITY-STATION-101.raw_turbidity \
  CLARIFIER-101.settled_turbidity \
  FILTER-QUALITY-STATION-101.filtered_turbidity \
  TRANSFER-OUTLET-QUALITY-STATION-101.outlet_turbidity \
  QUALITY-TRACEABILITY-ENGINE-101.outlet_quality_risk_score \
  QUALITY-TRACEABILITY-ENGINE-101.probable_root_cause_code
do
  val=$(curl -s "http://103.97.132.249:8000/api/v1/signals/$sid/current" \
    -H "X-API-Key: {EDGE_API_KEY}" | python -c "import sys,json; print(json.load(sys.stdin)['value'])" 2>/dev/null)
  echo "$sid = $val"
done
```

**Expected:**
- `raw_turbidity` > 60 NTU (spike from baseline)
- `settled_turbidity` rises proportionally
- `outlet_quality_risk_score` > 3
- `probable_root_cause_code` = 1 (raw_water_quality_event)

### Scenario 2: Chemical Overdosing

```bash
# 1. Switch
curl -s -X POST http://103.97.132.249:8100/api/v1/scenarios/chemical_overdosing
sleep 35

# 2. Verify: quality OK but cost high
echo "=== After chemical_overdosing ==="
for sid in \
  TRANSFER-OUTLET-QUALITY-STATION-101.outlet_turbidity \
  TRANSFER-OUTLET-QUALITY-STATION-101.outlet_free_chlorine \
  CHEMICAL-CONSUMPTION-STATION-101.chemical_cost_per_m3 \
  PLANT-KPI-101.cost_per_m3
do
  val=$(curl -s "http://103.97.132.249:8000/api/v1/signals/$sid/current" \
    -H "X-API-Key: {EDGE_API_KEY}" | python -c "import sys,json; print(json.load(sys.stdin)['value'])" 2>/dev/null)
  echo "$sid = $val"
done
```

**Expected:**
- `outlet_turbidity` remains acceptable (< 1.0 NTU)
- `chemical_cost_per_m3` > baseline (higher than normal)
- `cost_per_m3` elevated

### Scenario 3: Filter Clogging → Energy Impact

```bash
# 1. Switch
curl -s -X POST http://103.97.132.249:8100/api/v1/scenarios/filter_clogging_energy_impact
sleep 35

# 2. Verify
echo "=== After filter_clogging ==="
for sid in \
  FILTER-101.filter_dp \
  ENERGY-MONITORING-STATION-101.specific_energy_consumption \
  TRANSFER-OUTLET-QUALITY-STATION-101.outlet_turbidity \
  PLANT-KPI-101.cost_per_m3
do
  val=$(curl -s "http://103.97.132.249:8000/api/v1/signals/$sid/current" \
    -H "X-API-Key: {EDGE_API_KEY}" | python -c "import sys,json; print(json.load(sys.stdin)['value'])" 2>/dev/null)
  echo "$sid = $val"
done
```

**Expected:**
- `filter_dp` > 60 kPa (elevated)
- `specific_energy_consumption` > baseline
- `cost_per_m3` elevated

### Scenario 4: Chlorine Underdosing

```bash
curl -s -X POST http://103.97.132.249:8100/api/v1/scenarios/chlorine_underdosing
sleep 35

echo "=== After chlorine_underdosing ==="
for sid in \
  DISINFECTION-QUALITY-STATION-101.free_chlorine \
  TRANSFER-OUTLET-QUALITY-STATION-101.outlet_free_chlorine \
  TRANSFER-OUTLET-QUALITY-STATION-101.outlet_compliance_status
do
  val=$(curl -s "http://103.97.132.249:8000/api/v1/signals/$sid/current" \
    -H "X-API-Key: {EDGE_API_KEY}" | python -c "import sys,json; print(json.load(sys.stdin)['value'])" 2>/dev/null)
  echo "$sid = $val"
done
```

**Expected:**
- `free_chlorine` < 0.5 mg/L
- `outlet_free_chlorine` < 0.2 mg/L
- `outlet_compliance_status` = false

### Scenario 5: Filter Breakthrough

```bash
curl -s -X POST http://103.97.132.249:8100/api/v1/scenarios/filter_breakthrough
sleep 35

echo "=== After filter_breakthrough ==="
for sid in \
  FILTER-QUALITY-STATION-101.filtered_turbidity \
  TRANSFER-OUTLET-QUALITY-STATION-101.outlet_turbidity \
  QUALITY-TRACEABILITY-ENGINE-101.outlet_quality_risk_score
do
  val=$(curl -s "http://103.97.132.249:8000/api/v1/signals/$sid/current" \
    -H "X-API-Key: {EDGE_API_KEY}" | python -c "import sys,json; print(json.load(sys.stdin)['value'])" 2>/dev/null)
  echo "$sid = $val"
done
```

**Expected:**
- `filtered_turbidity` > 0.5 NTU
- `outlet_turbidity` > 0.5 NTU
- Risk score elevated

### Scenario 6: HSP Trip

```bash
curl -s -X POST http://103.97.132.249:8100/api/v1/scenarios/hsp_trip
sleep 35

echo "=== After hsp_trip ==="
for sid in \
  HSP-101.flow_rate \
  OUTLET-MANIFOLD-101.manifold_pressure \
  OUTLET-MANIFOLD-101.manifold_flow \
  HSP-102.flow_rate
do
  val=$(curl -s "http://103.97.132.249:8000/api/v1/signals/$sid/current" \
    -H "X-API-Key: {EDGE_API_KEY}" | python -c "import sys,json; print(json.load(sys.stdin)['value'])" 2>/dev/null)
  echo "$sid = $val"
done
```

**Expected:**
- `HSP-101.flow_rate` ≈ 0 (tripped)
- `manifold_pressure` drops
- `HSP-102.flow_rate` rises (compensating)

### Scenario 7: Algae Bloom

```bash
curl -s -X POST http://103.97.132.249:8100/api/v1/scenarios/algae_bloom
sleep 35

echo "=== After algae_bloom ==="
for sid in \
  RAW-WATER-QUALITY-STATION-101.raw_algae_index \
  DISINFECTION-QUALITY-STATION-101.free_chlorine \
  CHEMICAL-CONSUMPTION-STATION-101.chlorine_dose_rate
do
  val=$(curl -s "http://103.97.132.249:8000/api/v1/signals/$sid/current" \
    -H "X-API-Key: {EDGE_API_KEY}" | python -c "import sys,json; print(json.load(sys.stdin)['value'])" 2>/dev/null)
  echo "$sid = $val"
done
```

**Expected:**
- `raw_algae_index` elevated
- `free_chlorine` drops (increased demand)
- `chlorine_dose_rate` rises (compensating)

---

## Part C: Historian Trend Verification

### C1: Query historical data for turbidity chain

```bash
curl -s "http://103.97.132.249:8000/api/v1/historian/query" \
  -H "X-API-Key: {EDGE_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "signal_ids": [
      "RAW-WATER-QUALITY-STATION-101.raw_turbidity",
      "CLARIFIER-101.settled_turbidity",
      "FILTER-QUALITY-STATION-101.filtered_turbidity",
      "TRANSFER-OUTLET-QUALITY-STATION-101.outlet_turbidity"
    ],
    "from": "2026-07-02T00:00:00Z",
    "to": "2026-07-02T23:59:59Z",
    "limit": 100
  }' | python -c "
import sys, json
data = json.load(sys.stdin)
for sig_id in data:
    points = data[sig_id]
    if points:
        first = points[0]
        last = points[-1]
        print(f'{sig_id}: {len(points)} points | first={first[\"value\"]} @ {first[\"timestamp\"]} | last={last[\"value\"]} @ {last[\"timestamp\"]}')
    else:
        print(f'{sig_id}: NO DATA')
"
```

### C2: Verify data continuity

Check that each signal has data points and the timestamps are recent (within last hour).

---

## Part D: Return to Normal

```bash
curl -s -X POST http://103.97.132.249:8100/api/v1/scenarios/normal_operation
sleep 35
```

---

## Part E: Create E2E Test Report

Create file:
```text
docs/reference-models/wtp-demo-01-e2e-test-report.md
```

Template:

```markdown
# WTP-DEMO-01 End-to-End Demo Test Report

## Date
2026-07-02

## Baseline (Normal Operation)

| Signal | Value | Expected Range | Status |
|--------|-------|---------------|--------|
| raw_turbidity | ? | 30-60 NTU | ? |
| settled_turbidity | ? | 5-12 NTU | ? |
| filtered_turbidity | ? | 0.1-0.5 NTU | ? |
| outlet_turbidity | ? | 0.1-0.5 NTU | ? |
| cost_per_m3 | ? | 280-380 VND/m³ | ? |
| outlet_quality_risk_score | ? | 0-3 | ? |
| probable_root_cause_code | ? | 0 | ? |

## Scenario Results

### 1. Raw Water Contamination
| Check | Expected | Actual | Status |
|-------|----------|--------|--------|
| raw_turbidity spike | > 60 NTU | ? | ? |
| risk_score elevated | > 3 | ? | ? |
| root_cause_code | = 1 | ? | ? |

### 2. Chemical Overdosing
| Check | Expected | Actual | Status |
|-------|----------|--------|--------|
| Quality OK | outlet_turbidity < 1.0 | ? | ? |
| Cost elevated | chemical_cost > baseline | ? | ? |

### 3. Filter Clogging → Energy Impact
| Check | Expected | Actual | Status |
|-------|----------|--------|--------|
| filter_dp high | > 60 kPa | ? | ? |
| specific_energy high | > baseline | ? | ? |

### 4. Chlorine Underdosing
| Check | Expected | Actual | Status |
|-------|----------|--------|--------|
| free_chlorine low | < 0.5 mg/L | ? | ? |
| compliance fail | = false | ? | ? |

### 5. Filter Breakthrough
| Check | Expected | Actual | Status |
|-------|----------|--------|--------|
| filtered_turbidity high | > 0.5 NTU | ? | ? |
| risk elevated | > baseline | ? | ? |

### 6. HSP Trip
| Check | Expected | Actual | Status |
|-------|----------|--------|--------|
| HSP-101 flow ≈ 0 | tripped | ? | ? |
| HSP-102 compensates | flow rises | ? | ? |

### 7. Algae Bloom
| Check | Expected | Actual | Status |
|-------|----------|--------|--------|
| algae_index elevated | > baseline | ? | ? |
| chlorine demand up | dose_rate rises | ? | ? |

## Historian Verification
| Signal | Data Points | Latest Timestamp | Status |
|--------|------------|-----------------|--------|
| raw_turbidity | ? | ? | ? |
| settled_turbidity | ? | ? | ? |
| filtered_turbidity | ? | ? | ? |
| outlet_turbidity | ? | ? | ? |

## Traceability Verification
| Signal | Normal | Contamination | Overdosing | Status |
|--------|--------|--------------|------------|--------|
| outlet_quality_risk_score | ? | ? | ? | ? |
| probable_root_cause_code | 0 | 1 | ? | ? |

## Summary

| Criterion | Result |
|-----------|--------|
| 5+ abnormal scenarios tested | ?/8 |
| 3 mandatory scenarios verified | ?/3 |
| Turbidity chain visible | ? |
| Traceability signals respond | ? |
| Cost KPIs visible | ? |
| Historian queries work | ? |

## Issues
(List any issues found or "None")
```

---

## Deliverables

1. `docs/reference-models/wtp-demo-01-e2e-test-report.md` — Complete E2E report
2. All terminal output pasted into report

## Acceptance Criteria (from Phase 8A spec)

- [ ] 1. WTP contract validates successfully ✅ (done 8A-03)
- [ ] 2. Preview clean ✅ (done 8A-03)
- [ ] 3. Apply creates registry without breaking VF-DEMO ✅ (done 8A-04)
- [ ] 4. PlantOS shows correct areas/assets/signals ✅ (done 8A-04)
- [ ] 5. Simulator generates telemetry for ≥60 signals → NOW VERIFY
- [ ] 6. Measurement ingestion works → NOW VERIFY
- [ ] 7. Current/history query works → NOW VERIFY
- [ ] 8. Trend bundle: raw→settled→filtered→outlet turbidity → NOW VERIFY
- [ ] 9. Outlet quality and compliance signals visible → NOW VERIFY
- [ ] 10. Energy and chemical cost KPIs visible → NOW VERIFY
- [ ] 11. ≥5 abnormal scenarios demonstrable → NOW VERIFY
- [ ] 12. ≥5 alarm recommendations documented → NOW VERIFY
- [ ] 13. No VF-specific fields in core signal model ✅ (confirmed)
- [ ] 14. No new importer UI created ✅ (confirmed)
- [ ] 15. No automatic manifest generation ✅ (confirmed)

## Final Step: Cleanup

After all tests pass, return to normal:
```bash
curl -s -X POST http://103.97.132.249:8100/api/v1/scenarios/normal_operation
```
