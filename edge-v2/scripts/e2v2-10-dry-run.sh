#!/bin/bash
set -e

echo "=== E2V2-10 DRY-RUN ==="
echo "Started: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo ""

# ── Task 1: Pre-switch verification ──
echo "=== TASK 1: PRE-SWITCH VERIFICATION ==="
echo "v1: $(curl -s -o /dev/null -w '%{http_code}' http://localhost:8001)"
V2_STATUS=$(curl -s http://localhost:8011/api/status 2>/dev/null | python3 -c 'import sys,json;print(json.load(sys.stdin).get("status","?"))' 2>/dev/null)
echo "v2: $V2_STATUS"
echo "Center: $(curl -s -o /dev/null -w '%{http_code}' http://localhost:8000/health)"

V2_BACKLOG=$(curl -s http://localhost:8011/api/status 2>/dev/null | python3 -c 'import sys,json;print(json.load(sys.stdin).get("sync",{}).get("backlog","?"))' 2>/dev/null)
V2_BUFFER=$(curl -s http://localhost:8011/api/status 2>/dev/null | python3 -c 'import sys,json;print(json.load(sys.stdin).get("buffer",{}).get("rows","?"))' 2>/dev/null)
echo "v2 backlog: $V2_BACKLOG"
echo "v2 buffer rows: $V2_BUFFER"
echo ""

# ── Task 2: Shadow switch ──
echo "=== TASK 2: SHADOW SWITCH ==="
echo "v2 status:"
curl -s http://localhost:8011/api/status 2>/dev/null | python3 -c '
import sys,json
s=json.load(sys.stdin)
print("  connectors:")
for c_id,c_info in s.get("connectors",{}).items():
    print(f"    {c_id}: {c_info.get(\"status\",\"?\")}")
' 2>/dev/null || echo "  (could not parse connectors)"

echo ""
echo "v2 measurements in Center:"
V2_COUNT=$(curl -s "http://localhost:8000/api/v1/measurements/history?plant_id=EDGEV2-DEMO&limit=3" 2>/dev/null | python3 -c 'import sys,json;d=json.load(sys.stdin);print(len(d))' 2>/dev/null)
echo "  $V2_COUNT points"

echo "v1 measurements in Center:"
V1_COUNT=$(curl -s "http://localhost:8000/api/v1/measurements/history?plant_id=DEMO-PLANT&limit=3" 2>/dev/null | python3 -c 'import sys,json;d=json.load(sys.stdin);print(len(d))' 2>/dev/null)
echo "  $V1_COUNT points"
echo ""

echo "Edge nodes:"
curl -s http://localhost:8000/api/v1/edge-nodes 2>/dev/null | python3 -c '
import sys,json
d=json.load(sys.stdin)
for n in d if isinstance(d,list) else []:
    print(f"  {n[\"edge_node_id\"]}: {n.get(\"status\",\"?\")}")
' 2>/dev/null || echo "  (could not parse)"
echo ""

# ── Task 3: Comparison ──
echo "=== TASK 3: COMPARISON ==="
export PLANTOS_CENTER_PASSWORD='PlantOS@2026!'
cd /opt/plantos
python3 tools/compare_v1_v2_data.py \
  --hours 0.5 \
  --center-url http://localhost:8000 \
  --signal-ids PUMP-101.flow_rate PUMP-101.discharge_pressure MOTOR-101.motor_current
echo ""

# Save comparison report
COMPARISON_OUTPUT="/tmp/dry_run_comparison_$(date +%Y%m%d_%H%M%S).csv"
python3 tools/compare_v1_v2_data.py \
  --hours 0.5 \
  --center-url http://localhost:8000 \
  --signal-ids PUMP-101.flow_rate PUMP-101.discharge_pressure MOTOR-101.motor_current \
  --output "$COMPARISON_OUTPUT" 2>/dev/null || true
echo "Comparison saved: $COMPARISON_OUTPUT"
echo ""

# Timestamps
echo "v1 last timestamp:"
curl -s "http://localhost:8000/api/v1/measurements/history?plant_id=DEMO-PLANT&signal_id=PUMP-101.flow_rate&limit=1" 2>/dev/null | python3 -c 'import sys,json;d=json.load(sys.stdin);print(d[0].get("timestamp","?") if d else "NO DATA")' 2>/dev/null
echo "v2 last timestamp:"
curl -s "http://localhost:8000/api/v1/measurements/history?plant_id=EDGEV2-DEMO&signal_id=PUMP-101.flow_rate&limit=1" 2>/dev/null | python3 -c 'import sys,json;d=json.load(sys.stdin);print(d[0].get("timestamp","?") if d else "NO DATA")' 2>/dev/null
echo ""

# ── Task 4: Rollback ──
echo "=== TASK 4: ROLLBACK ==="
RECOVERY_START=$(date +%s)
echo "Stopping v2..."
docker compose -f /opt/plantos/deployment/docker-compose.yml stop plantos-edge-v2

echo "v1 after v2 stop: $(curl -s -o /dev/null -w '%{http_code}' http://localhost:8001)"

sleep 5
echo "Edge nodes after v2 stop:"
curl -s http://localhost:8000/api/v1/edge-nodes 2>/dev/null | python3 -c '
import sys,json
d=json.load(sys.stdin)
for n in d if isinstance(d,list) else []:
    print(f"  {n[\"edge_node_id\"]}: {n.get(\"status\",\"?\")}")
' 2>/dev/null

echo "v1 data flow after rollback:"
V1_POST=$(curl -s "http://localhost:8000/api/v1/measurements/history?plant_id=DEMO-PLANT&limit=3" 2>/dev/null | python3 -c 'import sys,json;d=json.load(sys.stdin);print(f"{len(d)} points")' 2>/dev/null)
echo "  $V1_POST"

RECOVERY_END=$(date +%s)
echo "Recovery time: $((RECOVERY_END - RECOVERY_START)) seconds"
echo ""

# Restore v2 to mirror mode
echo "Restarting v2 in mirror mode..."
docker compose -f /opt/plantos/deployment/docker-compose.yml start plantos-edge-v2
sleep 10
V2_RESTARTED=$(curl -s http://localhost:8011/api/status 2>/dev/null | python3 -c 'import sys,json;print(json.load(sys.stdin).get("status","?"))' 2>/dev/null)
echo "v2 after restart: $V2_RESTARTED"
echo ""

# ── Final state ──
echo "=== FINAL STATE ==="
echo "v1: $(curl -s -o /dev/null -w '%{http_code}' http://localhost:8001)"
echo "v2: $(curl -s http://localhost:8011/api/status 2>/dev/null | python3 -c 'import sys,json;print(json.load(sys.stdin).get("status","?"))' 2>/dev/null)"
echo "Center: $(curl -s -o /dev/null -w '%{http_code}' http://localhost:8000/health)"
echo ""
echo "=== DRY-RUN COMPLETE ==="
echo "Finished: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
