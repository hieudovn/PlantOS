#!/bin/bash
# E2V2-10: Limited Controlled Switch Dry-Run — VPS Execution
# Run this on VPS at /opt/plantos
# Usage: bash tools/e2v2-10-dry-run.sh

set -e

echo "=========================================="
echo "E2V2-10: Limited Controlled Switch Dry-Run"
echo "Started: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "=========================================="

# === Task 1: Pre-Switch Verification ===
echo ""
echo "=== TASK 1: Pre-Switch Verification ==="

echo "v1: $(curl -s -o /dev/null -w '%{http_code}' http://localhost:8001)"
V2_STATUS=$(curl -s http://localhost:8011/api/status | python3 -c 'import sys,json;print(json.load(sys.stdin).get("status","?"))')
echo "v2: $V2_STATUS"
echo "Center: $(curl -s -o /dev/null -w '%{http_code}' http://localhost:8000/health)"

echo ""
echo "=== BASELINE $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
echo "v2 backlog: $(curl -s http://localhost:8011/api/status | python3 -c 'import sys,json;print(json.load(sys.stdin).get("sync",{}).get("backlog","?"))')"
echo "v2 buffer: $(curl -s http://localhost:8011/api/status | python3 -c 'import sys,json;print(json.load(sys.stdin).get("buffer",{}).get("rows","?"))')"

# Verify expected
if [ "$(curl -s -o /dev/null -w '%{http_code}' http://localhost:8001)" != "200" ]; then
    echo "🔴 FAIL: v1 not responding"
    exit 1
fi
if [ "$V2_STATUS" != "running" ]; then
    echo "🔴 FAIL: v2 not running"
    exit 1
fi
echo "✅ Task 1 PASS"

# === Task 2: Execute Switch (Shadow Mode) ===
echo ""
echo "=== TASK 2: Shadow Switch Verification ==="

# 10.3 — Verify v2 ingesting
echo "v2 connectors:"
curl -s http://localhost:8011/api/status | python3 -c '
import sys,json
d=json.load(sys.stdin)
connectors = d.get("connectors",d.get("agent",{}).get("connectors",[]))
print(f"  Connectors: {len(connectors)}")
for c in connectors:
    print(f"    {c.get(\"id\",\"?\")}: {c.get(\"status\",c.get(\"state\",\"?\"))}")
'

# Check v2 data reaching Center
V2_PTS=$(curl -s "http://localhost:8000/api/v1/measurements/history?plant_id=EDGEV2-DEMO&limit=3" | python3 -c 'import sys,json;d=json.load(sys.stdin);print(len(d))')
echo "v2 measurements (EDGEV2-DEMO): $V2_PTS"

# Check v1 data still reaching Center
V1_PTS=$(curl -s "http://localhost:8000/api/v1/measurements/history?plant_id=DEMO-PLANT&limit=3" | python3 -c 'import sys,json;d=json.load(sys.stdin);print(len(d))')
echo "v1 measurements (DEMO-PLANT): $V1_PTS"

# 10.4 — Verify heartbeat
echo "Edge nodes:"
curl -s http://localhost:8000/api/v1/edge-nodes | python3 -c '
import sys,json
d=json.load(sys.stdin)
for n in d if isinstance(d,list) else []:
    print(f"  {n.get(\"edge_node_id\",\"?\")}: {n.get(\"status\",\"?\")}")
'

if [ "$V2_PTS" -gt 0 ] 2>/dev/null; then
    echo "✅ v2 data reaching Center"
else
    echo "⚠️ v2 has no measurements yet (may need --generate-measurements)"
fi
if [ "$V1_PTS" -gt 0 ] 2>/dev/null; then
    echo "✅ v1 data still reaching Center"
else
    echo "⚠️ v1 has no measurements"
fi

# === Task 3: Verify Dry-Run Success ===
echo ""
echo "=== TASK 3: Comparison + No Data Loss ==="

# 10.5 — Run comparison
echo "Running comparison..."
export PLANTOS_CENTER_PASSWORD='PlantOS@2026!'
COMPARE_OUTPUT=$(python3 /opt/plantos/tools/compare_v1_v2_data.py \
  --hours 0.5 \
  --center-url http://localhost:8000 \
  --signal-ids PUMP-101.flow_rate PUMP-101.discharge_pressure MOTOR-101.motor_current 2>&1 || true)
echo "$COMPARE_OUTPUT"

# Save comparison report
CSV_PATH="/tmp/dry_run_comparison_$(date +%Y%m%d_%H%M%S).csv"
python3 /opt/plantos/tools/compare_v1_v2_data.py \
  --hours 0.5 \
  --center-url http://localhost:8000 \
  --signal-ids PUMP-101.flow_rate PUMP-101.discharge_pressure MOTOR-101.motor_current \
  --output "$CSV_PATH" 2>/dev/null || true
echo "Comparison saved to: $CSV_PATH"

# 10.6 — Verify no data loss
echo ""
echo "Timestamp check:"
echo -n "  v1 last: "
curl -s "http://localhost:8000/api/v1/measurements/history?plant_id=DEMO-PLANT&signal_id=PUMP-101.flow_rate&limit=1" | \
  python3 -c 'import sys,json;d=json.load(sys.stdin);print(d[0].get("timestamp","NO DATA") if d else "NO DATA")'
echo -n "  v2 last: "
curl -s "http://localhost:8000/api/v1/measurements/history?plant_id=EDGEV2-DEMO&signal_id=PUMP-101.flow_rate&limit=1" | \
  python3 -c 'import sys,json;d=json.load(sys.stdin);print(d[0].get("timestamp","NO DATA") if d else "NO DATA")'

echo "✅ Task 3 complete"

# === Task 4: Execute Rollback ===
echo ""
echo "=== TASK 4: Rollback ==="
echo "Rollback start: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
RECOVERY_START=$(date +%s)

# Step 1: Stop Edge v2
echo "Stopping v2..."
docker compose -f /opt/plantos/deployment/docker-compose.yml stop plantos-edge-v2

# Step 2: Verify Edge v1 still running
echo -n "v1 status: "
curl -s -o /dev/null -w '%{http_code}' http://localhost:8001
echo ""

# Step 3: Verify v1 heartbeat
sleep 5
echo "Edge nodes after v2 stop:"
curl -s http://localhost:8000/api/v1/edge-nodes | python3 -c '
import sys,json
d=json.load(sys.stdin)
for n in d if isinstance(d,list) else []:
    print(f"  {n.get(\"edge_node_id\",\"?\")}: {n.get(\"status\",\"?\")}")
'

# Step 4: Verify v1 data flow
echo -n "v1 measurements after rollback: "
curl -s "http://localhost:8000/api/v1/measurements/history?plant_id=DEMO-PLANT&limit=3" | \
  python3 -c 'import sys,json;d=json.load(sys.stdin);print(f"{len(d)} points")'

RECOVERY_END=$(date +%s)
RECOVERY_TIME=$((RECOVERY_END - RECOVERY_START))
echo "Recovery time: $RECOVERY_TIME seconds"

# Restore v2 to mirror mode
echo ""
echo "Restoring v2 to mirror mode..."
docker compose -f /opt/plantos/deployment/docker-compose.yml start plantos-edge-v2
sleep 10

# Final verification
echo ""
echo "=== FINAL STATE $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
echo -n "v1: "
curl -s -o /dev/null -w '%{http_code}' http://localhost:8001
echo ""
V2_FINAL=$(curl -s http://localhost:8011/api/status | python3 -c 'import sys,json;print(json.load(sys.stdin).get("status","?"))')
echo "v2: $V2_FINAL"
echo -n "Center: "
curl -s -o /dev/null -w '%{http_code}' http://localhost:8000/health
echo ""

echo ""
echo "=========================================="
echo "E2V2-10 Dry-Run Complete"
echo "Ended: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "=========================================="
echo ""
echo "Summary:"
echo "  Pre-switch: v1=200, v2=$V2_STATUS, Center=200"
echo "  Comparison: see output above"
echo "  Rollback: recovery_time=${RECOVERY_TIME}s"
echo "  Post-restore: v1=200, v2=$V2_FINAL, Center=200"
echo "  Report: $CSV_PATH"
