#!/bin/bash
# E2V2-13 Extended Monitoring — 8 iterations x 30 min = 4 hours
MAX_ITER=8
OUTPUT="/opt/plantos/edge-v2/data/e2v2-13-monitor.csv"
echo "timestamp,v1_code,v2_status,v2_backlog,v2_buffer,connector_ok,heartbeat_ok,center_code" > "$OUTPUT"

for i in $(seq 1 $MAX_ITER); do
  TS=$(date -u +%Y-%m-%dT%H:%M:%SZ)
  V1=$(curl -s -o /dev/null -w '%{http_code}' http://localhost:8001)
  V2=$(curl -s http://localhost:8011/api/status)
  V2_STATUS=$(echo "$V2" | python3 -c 'import sys,json;print(json.load(sys.stdin)["status"])')
  V2_BL=$(echo "$V2" | python3 -c 'import sys,json;print(json.load(sys.stdin)["sync"]["backlog"])')
  V2_BUF=$(echo "$V2" | python3 -c 'import sys,json;print(json.load(sys.stdin)["buffer"]["row_count"])')
  CONN=$(echo "$V2" | python3 -c 'import sys,json;d=json.load(sys.stdin);cs=d["connectors"]["list"];print(sum(1 for c in cs if c["status"]=="running"))')
  CENTER=$(curl -s -o /dev/null -w '%{http_code}' http://localhost:8000)
  echo "$TS,$V1,$V2_STATUS,$V2_BL,$V2_BUF,$CONN,,$CENTER" >> "$OUTPUT"
  echo "[$TS] Iter $i/$MAX_ITER: v1=$V1 v2=$V2_STATUS bl=$V2_BL buf=$V2_BUF conn=$CONN center=$CENTER"
  if [ $i -lt $MAX_ITER ]; then sleep 1800; fi
done
echo "Monitoring complete. Results: $OUTPUT"
