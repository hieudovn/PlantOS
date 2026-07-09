# E2V2-10: Limited Controlled Switch Dry-Run — VPS Execution

> **SA Gate:** ✅ APPROVED 2026-07-09
> **Role:** Coder-Executioner — run ONLY on VPS (103.97.132.249)
> **Constraint:** Edge v1 remains PRIMARY. Production switch NOT approved.
> **Scope:** Dry-run only — test switch procedure, then rollback immediately.

## Prerequisites

```
VPS: 103.97.132.249
Repo: /opt/plantos
Center: http://localhost:8000 (JWT auth)
Edge v1: http://localhost:8001 (DEMO-PLANT, MUST stay running)
Edge v2: http://localhost:8011 (EDGEV2-DEMO, Docker)
```

Ensure `PLANTOS_CENTER_PASSWORD` is set:

```bash
export PLANTOS_CENTER_PASSWORD='PlantOS@2026!'
```

---

## Execution Steps

### Task 1: Pre-Switch Verification

```bash
# 10.1 — Verify all services healthy
echo "v1: $(curl -s -o /dev/null -w '%{http_code}' http://localhost:8001)"
echo "v2: $(curl -s http://localhost:8011/api/status | python3 -c 'import sys,json;print(json.load(sys.stdin).get(\"status\",\"?\"))')"
echo "Center: $(curl -s -o /dev/null -w '%{http_code}' http://localhost:8000/health)"

# 10.2 — Record baseline
echo "=== BASELINE $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
echo "v2 backlog: $(curl -s http://localhost:8011/api/status | python3 -c 'import sys,json;print(json.load(sys.stdin).get(\"sync\",{}).get(\"backlog\",\"?\"))')"
echo "v2 buffer: $(curl -s http://localhost:8011/api/status | python3 -c 'import sys,json;print(json.load(sys.stdin).get(\"buffer\",{}).get(\"rows\",\"?\"))')"
```

**Expected:**
```
v1: 200
v2: running
Center: 200
v2 backlog: < 50
v2 buffer: < 1000
```

---

### Task 2: Execute Switch (Shadow Mode)

This is a **shadow switch** — v2 acts as if it were primary, but v1 continues running.

```bash
# 10.3 — Verify v2 is actively ingesting
# Check v2 status shows connected connectors
curl -s http://localhost:8011/api/status | python3 -m json.tool

# Check v2 data is reaching Center
curl -s "http://localhost:8000/api/v1/measurements/history?plant_id=EDGEV2-DEMO&limit=3" | \
  python3 -c "import sys,json;d=json.load(sys.stdin);print(f'v2 measurements: {len(d)}')"

# Check v1 data still reaching Center (must be unchanged)
curl -s "http://localhost:8000/api/v1/measurements/history?plant_id=DEMO-PLANT&limit=3" | \
  python3 -c "import sys,json;d=json.load(sys.stdin);print(f'v1 measurements: {len(d)}')"

# 10.4 — Verify heartbeat
curl -s http://localhost:8000/api/v1/edge-nodes | \
  python3 -c "import sys,json;d=json.load(sys.stdin);[print(f'  {n[\"edge_node_id\"]}: {n.get(\"status\",\"?\")}') for n in d if isinstance(d,list)]"
```

**Expected:**
```
v2 measurements: > 0
v1 measurements: > 0 (unchanged)
Edge nodes:
  edge-agent-01: online
  EDGEV2-PC-01: online
```

---

### Task 3: Verify Dry-Run Success

```bash
# 10.5 — Run comparison during shadow mode
python3 /opt/plantos/tools/compare_v1_v2_data.py \
  --hours 0.5 \
  --center-url http://localhost:8000 \
  --signal-ids PUMP-101.flow_rate PUMP-101.discharge_pressure MOTOR-101.motor_current

# Save comparison report
python3 /opt/plantos/tools/compare_v1_v2_data.py \
  --hours 0.5 \
  --center-url http://localhost:8000 \
  --signal-ids PUMP-101.flow_rate PUMP-101.discharge_pressure MOTOR-101.motor_current \
  --output /tmp/dry_run_comparison_$(date +%Y%m%d_%H%M%S).csv
```

**Expected:**
```
Results: 3 PASS, 0 FAIL, 0 WARN, 0 SKIP
✅ All shared signals within tolerance.
```

```bash
# 10.6 — Verify no data loss
echo "v1 last timestamp:"
curl -s "http://localhost:8000/api/v1/measurements/history?plant_id=DEMO-PLANT&signal_id=PUMP-101.flow_rate&limit=1" | \
  python3 -c "import sys,json;d=json.load(sys.stdin);print(d[0].get('timestamp','?') if d else 'NO DATA')"

echo "v2 last timestamp:"
curl -s "http://localhost:8000/api/v1/measurements/history?plant_id=EDGEV2-DEMO&signal_id=PUMP-101.flow_rate&limit=1" | \
  python3 -c "import sys,json;d=json.load(sys.stdin);print(d[0].get('timestamp','?') if d else 'NO DATA')"
```

**Expected:** Both show timestamps within the last 60 seconds.

---

### Task 4: Execute Rollback

```bash
# 10.7 — Follow rollback runbook
echo "=== ROLLBACK $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
RECOVERY_START=$(date +%s)

# Step 1: Stop Edge v2
echo "Stopping v2..."
docker compose -f /opt/plantos/deployment/docker-compose.yml stop plantos-edge-v2

# Step 2: Verify Edge v1 still running (was never stopped)
echo "v1 status: $(curl -s -o /dev/null -w '%{http_code}' http://localhost:8001)"

# Step 3: Verify v1 heartbeat reaches Center
sleep 5
curl -s http://localhost:8000/api/v1/edge-nodes | \
  python3 -c "import sys,json;d=json.load(sys.stdin);[print(f'  {n[\"edge_node_id\"]}: {n.get(\"status\",\"?\")}') for n in d if isinstance(d,list)]"

# Step 4: Verify v1 data flow
echo "v1 measurements after rollback:"
curl -s "http://localhost:8000/api/v1/measurements/history?plant_id=DEMO-PLANT&limit=3" | \
  python3 -c "import sys,json;d=json.load(sys.stdin);print(f'{len(d)} points')"

RECOVERY_END=$(date +%s)
echo "Recovery time: $((RECOVERY_END - RECOVERY_START)) seconds"
```

**Expected:**
```
v1 status: 200
edge-agent-01: online
EDGEV2-PC-01: offline (expected — v2 stopped)
v1 measurements: > 0
Recovery time: < 60 seconds
```

```bash
# 10.8 — Restore v2 to mirror mode
echo "Restarting v2 in mirror mode..."
docker compose -f /opt/plantos/deployment/docker-compose.yml start plantos-edge-v2

# Wait for v2 to be healthy
sleep 10
echo "v2 status: $(curl -s http://localhost:8011/api/status | python3 -c 'import sys,json;print(json.load(sys.stdin).get(\"status\",\"?\"))')"

# Final verification — both healthy
echo "=== FINAL STATE $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
echo "v1: $(curl -s -o /dev/null -w '%{http_code}' http://localhost:8001)"
echo "v2: $(curl -s http://localhost:8011/api/status | python3 -c 'import sys,json;print(json.load(sys.stdin).get(\"status\",\"?\"))')"
echo "Center: $(curl -s -o /dev/null -w '%{http_code}' http://localhost:8000/health)"
```

**Expected:**
```
v2 status: running
v1: 200
v2: running
Center: 200
```

---

## Evidence to Collect

Copy all evidence back to local machine:

```bash
# From local:
scp root@103.97.132.249:/tmp/dry_run_comparison_*.csv edge-v2/data/
```

Save terminal output to `docs/reports/e2v2-10-dry-run-evidence.md` (or append to readiness report).

---

## Red Flags

- 🔴 STOP if v1 affected in any way (v1 must be at 200 throughout)
- 🔴 STOP if v2 shadow switch causes data loss or gap > 30s
- 🔴 STOP if rollback fails to restore state within 60s
- 🔴 STOP if comparison shows any deviation > 5%

## Recovery (if anything goes wrong)

```bash
# Emergency: just ensure v1 is running
curl http://localhost:8001  # If NOT 200 → this is a CRITICAL failure
docker compose -f /opt/plantos/deployment/docker-compose.yml start plantos-edge-v2
```

## Expected Timeline

| Step | Duration |
|---|---|
| Pre-check | 2 min |
| Shadow switch verification | 5 min |
| Comparison run | 2 min |
| Rollback | 1 min |
| Restore v2 | 1 min |
| **Total** | **~11 min** |
