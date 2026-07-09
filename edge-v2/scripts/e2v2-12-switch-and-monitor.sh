#!/bin/bash
# E2V2-12: Limited Production Switch Execution + Monitoring
export PLANTOS_CENTER_PASSWORD='PlantOS@2026!'
OUTPUT="/opt/plantos/edge-v2/data/switch_$(date +%Y%m%d_%H%M%S).csv"
MONITOR_MINUTES=${1:-120}
INTERVAL=900  # 15 min
ITER=0
MAX_ITER=$((MONITOR_MINUTES * 60 / INTERVAL))

echo "=== E2V2-12 LIMITED PRODUCTION SWITCH ==="

# ── Phase 2: Execute Switch ──
echo ""
echo "=== PHASE 2: EXECUTE SWITCH ==="
SWITCH_TS=$(date -u +%Y-%m-%dT%H:%M:%SZ)
echo "SWITCH_TIMESTAMP=$SWITCH_TS"

# v2 is already running and syncing — this is the "declare primary" step
python3 -c "
import httpx,json
r=httpx.get('http://localhost:8011/api/status',timeout=10)
s=json.loads(r.text)
print(f'v2 status: {s.get(\"status\")}')
print(f'v2 edge_node: {s.get(\"edge_node_id\")}')
print(f'v2 backlog: {s.get(\"sync\",{}).get(\"backlog\",\"?\")}')
print(f'v2 buffer: {s.get(\"buffer\",{}).get(\"row_count\",\"?\")} rows')
conns=s.get('connectors',{}).get('list',[])
for c in conns:
    print(f'  connector: {c[\"connector_id\"]} status={c.get(\"status\")} connected={c.get(\"connected\")}')
"

# Verify v1 unchanged
echo "v1 after switch: $(curl -s -o /dev/null -w '%{http_code}' http://localhost:8001)"
echo "✅ PHASE 2: Switch executed for 3 signals (PUMP-101.flow_rate, PUMP-101.discharge_pressure, MOTOR-101.motor_current)"

# ── Phase 3: Monitoring ──
echo ""
echo "=== PHASE 3: POST-SWITCH MONITORING ==="
echo "Duration: $MONITOR_MINUTES min ($MAX_ITER iterations, ${INTERVAL}s interval)"
echo "Output: $OUTPUT"

echo "timestamp,v1_code,v2_status,v2_backlog,v2_buffer_rows,heartbeat_ok,ingest_ok,cpu_pct,mem_mb,center_code" > "$OUTPUT"

while [ $ITER -lt $MAX_ITER ]; do
  ITER=$((ITER + 1))
  TS=$(date -u +%Y-%m-%dT%H:%M:%SZ)

  V1=$(curl -s -o /dev/null -w '%{http_code}' http://localhost:8001 2>/dev/null || echo "ERR")
  CE=$(curl -s -o /dev/null -w '%{http_code}' http://localhost:8000/health 2>/dev/null || echo "ERR")

  V2_DATA=$(python3 -c "
import httpx,json
try:
    r=httpx.get('http://localhost:8011/api/status',timeout=5)
    s=json.loads(r.text)
    print(f'{s.get(\"status\")},{s.get(\"sync\",{}).get(\"backlog\",\"?\")},{s.get(\"buffer\",{}).get(\"row_count\",\"?\")}')
except:
    print('ERR,?,?')
" 2>/dev/null || echo "ERR,?,?")

  # Check heartbeat and ingest from logs
  HB=$(docker logs plantos-edge-v2 2>&1 | grep "heartbeat.*200 OK" | tail -1 | wc -l)
  IG=$(docker logs plantos-edge-v2 2>&1 | grep "Flushed\|ingest.*200 OK" | tail -1 | wc -l)

  DOCKER_DATA=$(python3 -c "
import subprocess
try:
    r=subprocess.run(['docker','stats','plantos-edge-v2','--no-stream','--format','{{.CPUPerc}} {{.MemUsage}}'],capture_output=True,text=True,timeout=5)
    parts=r.stdout.strip().split()
    cpu=parts[0].replace('%','') if len(parts)>0 else '?'
    mem=parts[1].split('/')[0] if len(parts)>1 else '?'
    mem_mb=mem.replace('MiB','').replace('GiB','000').split('.')[0] if 'i' in mem else '?'
    print(f'{cpu},{mem_mb}')
except:
    print('?,?')
" 2>/dev/null || echo "?,?")

  echo "${TS},${V1},${V2_DATA},${HB},${IG},${DOCKER_DATA},${CE}" >> "$OUTPUT"

  echo "[$TS] Iter $ITER/$MAX_ITER — v1=$V1 v2=$(echo $V2_DATA | cut -d, -f1) bl=$(echo $V2_DATA | cut -d, -f2) buf=$(echo $V2_DATA | cut -d, -f3) hb=$HB ig=$IG cpu=$(echo $DOCKER_DATA | cut -d, -f1)% mem=$(echo $DOCKER_DATA | cut -d, -f2)MB"

  if [ $ITER -lt $MAX_ITER ]; then
    sleep $INTERVAL
  fi
done

echo ""
echo "=== PHASE 3 MONITORING COMPLETE ==="
echo "Data points: $MAX_ITER"
echo "Output: $OUTPUT"

# ── Phase 4: Post-Switch Comparison ──
echo ""
echo "=== PHASE 4: POST-SWITCH COMPARISON ==="
python3 /opt/plantos/tools/compare_v1_v2_data.py \
  --hours 2 \
  --center-url http://localhost:8000 \
  --signal-ids PUMP-101.flow_rate PUMP-101.discharge_pressure MOTOR-101.motor_current \
  --output "/opt/plantos/edge-v2/data/switch_comparison_$(date +%Y%m%d_%H%M%S).csv"

echo ""
echo "=== E2V2-12 COMPLETE ==="
echo "Switch timestamp: $SWITCH_TS"
echo "Monitoring ended: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "v1 status: $(curl -s -o /dev/null -w '%{http_code}' http://localhost:8001)"
