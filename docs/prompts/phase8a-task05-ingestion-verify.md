# Task 8A-05 — Verify WTP Ingestion & Fix OPC UA Bindings

## Context

You are the Coder-Executioner for PlantOS Phase 8A.

**Great news from VF:** The WTP simulator is already running and pushing data via HTTP ingestion!

```
VF Simulator → POST http://103.97.132.249:8000/api/v1/measurements/ingest
Status: connected, 0 errors
Rate: 1 frame/sec (92 measurements/frame)
Source: wtp-sim-01
```

Your job: Verify data is flowing correctly, and fix the OPC UA bindings in the contract to match the VF simulator's actual NodeId convention.

## Required Reading

```text
docs/reference-models/wtp-demo-01-apply-report.md        ← Know what was applied
docs/reference-models/wtp-demo-01-design.md               ← Know what to verify
```

## Part A: Verify Ingestion

### A1: Check VF ingestion status

```bash
# Check backend logs for ingestion activity
ssh root@103.97.132.249 "docker logs plantos-backend --tail 100 2>&1 | grep -i -E 'wtp|ingest|measurement' | tail -20"
```

### A2: Query current values for key signals

```bash
# Test 1: Raw water quality
curl -s "http://103.97.132.249:8000/api/v1/signals/RAW-WATER-QUALITY-STATION-101.raw_turbidity/current" \
  -H "X-API-Key: {EDGE_API_KEY}" | python -m json.tool

# Test 2: Settled water quality
curl -s "http://103.97.132.249:8000/api/v1/signals/CLARIFIER-101.settled_turbidity/current" \
  -H "X-API-Key: {EDGE_API_KEY}" | python -m json.tool

# Test 3: Filtered water quality
curl -s "http://103.97.132.249:8000/api/v1/signals/FILTER-QUALITY-STATION-101.filtered_turbidity/current" \
  -H "X-API-Key: {EDGE_API_KEY}" | python -m json.tool

# Test 4: Outlet quality
curl -s "http://103.97.132.249:8000/api/v1/signals/TRANSFER-OUTLET-QUALITY-STATION-101.outlet_turbidity/current" \
  -H "X-API-Key: {EDGE_API_KEY}" | python -m json.tool

# Test 5: Cost KPI
curl -s "http://103.97.132.249:8000/api/v1/signals/PLANT-KPI-101.cost_per_m3/current" \
  -H "X-API-Key: {EDGE_API_KEY}" | python -m json.tool
```

Expected: Each returns a JSON with `signal_id`, `value`, `timestamp`, `quality`.

> **Note:** If `/current` endpoint doesn't exist, try the historian query:
> ```bash
> curl -s "http://103.97.132.249:8000/api/v1/historian/query" \
>   -H "X-API-Key: {EDGE_API_KEY}" \
>   -H "Content-Type: application/json" \
>   -d '{"signal_ids":["RAW-WATER-QUALITY-STATION-101.raw_turbidity"],"limit":1}'
> ```

### A3: Verify the turbidity chain

Query all 4 turbidity signals at once:

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
    "limit": 5
  }' | python -m json.tool
```

Verify the treatment chain relationship:
- `raw_turbidity` should be highest (e.g., 30-60 NTU)
- `settled_turbidity` should be ~15-20% of raw (e.g., 5-12 NTU)
- `filtered_turbidity` should be very low (e.g., 0.1-0.5 NTU)
- `outlet_turbidity` should be similar to filtered (e.g., 0.1-0.5 NTU)

### A4: Sample 10 random signals

```bash
python -c "
import requests, json, random

signals = [
    'RWP-101.flow_rate', 'RWP-101-MOTOR.motor_current',
    'COAG-PUMP-101.flow_rate', 'CHLORINE-PUMP-101.flow_rate',
    'FILTER-101.filter_dp', 'FILTER-102.filter_dp',
    'DISINFECTION-QUALITY-STATION-101.free_chlorine',
    'ENERGY-MONITORING-STATION-101.total_active_power',
    'PLANT-KPI-101.water_production_today',
    'QUALITY-TRACEABILITY-ENGINE-101.outlet_quality_risk_score',
]
for sid in signals:
    try:
        r = requests.get(
            f'http://103.97.132.249:8000/api/v1/signals/{sid}/current',
            headers={'X-API-Key': '{EDGE_API_KEY}'},
            timeout=5
        )
        if r.status_code == 200:
            d = r.json()
            print(f'✅ {sid}: {d.get(\"value\")} ({d.get(\"timestamp\", \"?\")})')
        else:
            print(f'❌ {sid}: HTTP {r.status_code}')
    except Exception as e:
        print(f'❌ {sid}: {e}')
"
```

Expected: At least 8/10 should return valid values. If most fail, ingestion may not be active.

## Part B: Fix OPC UA Bindings

### B1: The Problem

The contract has 9 OPC UA bindings using the old convention:
```yaml
- {signal_id: RWP-101.flow_rate, node_id: ns=2;s=RWP101_FLOW_RATE}  ← OLD
```

The VF WTP simulator uses the signal_id directly as NodeId:
```
ns=2;s=RWP-101.flow_rate  ← CORRECT (VF convention)
```

### B2: Fix the contract bindings

Replace ALL 9 existing bindings with the correct NodeId format:

```yaml
bindings:
  opcua:
    - {signal_id: RWP-101.flow_rate, node_id: ns=2;s=RWP-101.flow_rate, scale: 1.0, offset: 0.0}
    - {signal_id: RWP-101-MOTOR.motor_current, node_id: ns=2;s=RWP-101-MOTOR.motor_current, scale: 1.0, offset: 0.0}
    - {signal_id: COAG-PUMP-101.flow_rate, node_id: ns=2;s=COAG-PUMP-101.flow_rate, scale: 1.0, offset: 0.0}
    - {signal_id: CLARIFIER-101.settled_turbidity, node_id: ns=2;s=CLARIFIER-101.settled_turbidity, scale: 1.0, offset: 0.0}
    - {signal_id: FILTER-101.filter_dp, node_id: ns=2;s=FILTER-101.filter_dp, scale: 1.0, offset: 0.0}
    - {signal_id: FILTER-QUALITY-STATION-101.filtered_turbidity, node_id: ns=2;s=FILTER-QUALITY-STATION-101.filtered_turbidity, scale: 1.0, offset: 0.0}
    - {signal_id: TRANSFER-OUTLET-QUALITY-STATION-101.outlet_turbidity, node_id: ns=2;s=TRANSFER-OUTLET-QUALITY-STATION-101.outlet_turbidity, scale: 1.0, offset: 0.0}
    - {signal_id: HSP-101-MOTOR.motor_current, node_id: ns=2;s=HSP-101-MOTOR.motor_current, scale: 1.0, offset: 0.0}
    - {signal_id: ENERGY-MONITORING-STATION-101.total_active_power, node_id: ns=2;s=ENERGY-MONITORING-STATION-101.total_active_power, scale: 1.0, offset: 0.0}
```

### B3: Update validator to accept new NodeId format

The V11 validation rule in `validator.py` currently requires:
```python
OPCUA_NODE_PATTERN = re.compile(r"^ns=\d+;s=[A-Z][A-Z0-9_]*$")
```

This rejects NodeIds with dots (`.`) and lowercase letters. Fix:

```python
# In backend/app/modules/contracts/validator.py, change:
OPCUA_NODE_PATTERN = re.compile(r"^ns=\d+;s=[A-Z][A-Z0-9_]*$")
# To:
OPCUA_NODE_PATTERN = re.compile(r"^ns=\d+;s=[A-Za-z][A-Za-z0-9_.-]*$")
```

Then re-run backend or redeploy.

### B4: Validate after fix

```bash
python -c "
import yaml
import sys
sys.path.insert(0, 'backend')
from app.modules.contracts.schemas import ContractV2
from app.modules.contracts.validator import validate_contract

with open('examples/contracts/wtp-demo-01.contract.yaml') as f:
    data = yaml.safe_load(f)

contract = ContractV2(**data)
result = validate_contract(data)

print(f'Errors: {len(result.errors)}')
for e in result.errors:
    print(f'  ERROR: {e}')
print(f'Warnings: {len(result.warnings)}')

# Specifically check V11 no longer fails
opcua = (data.get('bindings') or {}).get('opcua', [])
for b in opcua:
    print(f'  OPC UA: {b[\"signal_id\"]} → {b[\"node_id\"]}')
print()
print('✅ PASS' if result.valid else '❌ FAIL')
"
```

## Part C: Verify VF Scenario Control

### C1: List scenarios

```bash
curl -s http://103.97.132.249:8100/api/v1/scenarios | python -m json.tool
```

### C2: Check current scenario

```bash
curl -s http://103.97.132.249:8100/api/v1/scenarios/current | python -m json.tool
```

### C3: Switch to raw_water_contamination

```bash
curl -s -X POST http://103.97.132.249:8100/api/v1/scenarios/raw_water_contamination | python -m json.tool
```

Wait 30 seconds for transition, then check turbidity values:
```bash
curl -s "http://103.97.132.249:8000/api/v1/signals/RAW-WATER-QUALITY-STATION-101.raw_turbidity/current" \
  -H "X-API-Key: {EDGE_API_KEY}" | python -m json.tool
```

Expected: raw_turbidity should spike significantly higher (e.g., 80-120 NTU vs normal 30-50).

### C4: Switch back to normal

```bash
curl -s -X POST http://103.97.132.249:8100/api/v1/scenarios/normal_operation | python -m json.tool
```

## Deliverables

1. Updated `examples/contracts/wtp-demo-01.contract.yaml` with corrected OPC UA bindings
2. Updated `backend/app/modules/contracts/validator.py` with relaxed V11 pattern
3. Ingestion verification results (paste terminal output)
4. Scenario switch test results

## Report Format

Create or append to a verification log. No need for a formal report file — paste results directly for PM review.

## Acceptance Criteria

- [ ] 8/10 current value queries return valid data
- [ ] Turbidity chain shows correct treatment relationship
- [ ] OPC UA bindings match VF convention
- [ ] V11 validation passes with new NodeId format
- [ ] Scenario switch works and affects values
- [ ] Contract re-validates with 0 errors
