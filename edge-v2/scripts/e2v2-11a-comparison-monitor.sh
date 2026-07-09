#!/bin/bash
# E2V2-11A: Extended comparison monitor
# Runs comparison every 30 min for N iterations
MAX_ITER=${1:-8}
ITER=0
export PLANTOS_CENTER_PASSWORD='PlantOS@2026!'
API="http://localhost:8000"
OUTPUT_DIR="/opt/plantos/edge-v2/data"
mkdir -p "$OUTPUT_DIR"

echo "=== E2V2-11A Extended Comparison Monitor ==="
echo "Max iterations: $MAX_ITER (est. $((MAX_ITER * 30 / 60)) hours)"
echo "Started: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo ""

while [ $ITER -lt $MAX_ITER ]; do
  ITER=$((ITER + 1))
  TS=$(date -u +%Y%m%d_%H%M%S)
  echo "[$TS] Iteration $ITER/$MAX_ITER"

  python3 /opt/plantos/tools/compare_v1_v2_data.py \
    --hours 0.5 \
    --center-url "$API" \
    --output "$OUTPUT_DIR/comparison_${TS}.csv" \
    --signal-ids PUMP-101.flow_rate PUMP-101.discharge_pressure MOTOR-101.motor_current

  python3 -c "
import httpx, json
r = httpx.get('http://localhost:8011/api/status', timeout=10)
s = json.loads(r.text)
print(f'  status={s.get(\"status\")} backlog={s.get(\"sync\",{}).get(\"backlog\",\"?\")}')
"

  V1=$(curl -s -o /dev/null -w '%{http_code}' http://localhost:8001)
  CE=$(curl -s -o /dev/null -w '%{http_code}' http://localhost:8000/health)
  echo "  v1=$V1 Center=$CE"
  echo ""

  if [ $ITER -lt $MAX_ITER ]; then
    sleep 1800
  fi
done

echo "=== COMPARISON MONITOR COMPLETE ==="
echo "Finished: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
