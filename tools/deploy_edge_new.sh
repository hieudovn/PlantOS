#!/bin/bash
set -e
SHA=801e952

echo "=== Step 1: Build Edge v2 ==="
cd /opt/plantos
git fetch origin phase8-closure 2>/dev/null
git checkout -f --detach $SHA 2>/dev/null || true
echo "CHECKOUT: $(git rev-parse --short=7 HEAD)"

docker build -t plantos-edge-v2:$SHA -f edge-v2/Dockerfile . 2>&1 | tail -5

echo "=== Step 2: Prepare config ==="
# Copy the working config (already has correct api_key, center_url)
cp /opt/plantos/edge-v2/agent/config/config.edge-v2.yaml /tmp/edge_config.yaml

# Ensure center_url is correct
python3 -c "
c=open('/tmp/edge_config.yaml').read()
c=c.replace('center_url: http://backend:8000','center_url: http://plantos-backend:8000')
c=c.replace('center_url: http://172.19.0.1:8000','center_url: http://plantos-backend:8000')
c=c.replace('center_url: http://localhost:8000','center_url: http://plantos-backend:8000')
open('/tmp/edge_config.yaml','w').write(c)
print('CONFIG_UPDATED')
"
grep center_url /tmp/edge_config.yaml

echo "=== Step 3: Swap Edge v2 ==="
docker stop plantos-edge-v2 2>/dev/null || true
docker rm plantos-edge-v2 2>/dev/null || true

docker run -d --name plantos-edge-v2 \
  --network deployment_plantos-net \
  -p 127.0.0.1:8011:8011 \
  -v /tmp/edge_config.yaml:/app/agent/config/config.edge-v2.yaml:ro \
  -e EDGE_CONFIG_PATH=/app/agent/config/config.edge-v2.yaml \
  -e EDGE_SESSION_SECRET=ci-test-session-secret-min-32-bytes!! \
  plantos-edge-v2:$SHA

echo "=== Step 4: Verify ==="
sleep 12
echo "--- Edge Log ---"
docker logs plantos-edge-v2 --tail 20 2>&1 | grep -E 'JWT|heart|poll|connector|ingest|error|start|login'

echo ""
echo "--- Backend Ingest ---"
docker logs plantos-backend --tail 5 2>&1 | grep -E 'ingest|20[01]'

echo ""
echo "--- Edge Buffer ---"
curl -s http://localhost:8011/api/status 2>&1 | python3 -c "
import sys,json
d=json.load(sys.stdin)
b=d.get('buffer',{})
print(f'Buffer: {b.get(\"row_count\",0)} rows')
print(f'Status: {d.get(\"status\")}')
print(f'Uptime: {d.get(\"uptime_seconds\")}s')
" 2>&1

echo ""
echo "=== Step 5: Seed live data ==="
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login -H 'Content-Type: application/json' -d '{"username":"admin","password":"PlantOS@2026!"}' | python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token',''))")

# Send current-time measurements for common signals
for sig in "COMP01-MOTOR.current" "COMP01-MOTOR.winding_temp" "PUMP-101.flow_rate"; do
  TS=$(date -u +%Y-%m-%dT%H:%M:%SZ)
  VAL=$(python3 -c "import random; print(round(random.uniform(10,150),2))")
  curl -s -X POST http://localhost:8000/api/v1/measurements/ingest \
    -H "Authorization: Bearer $TOKEN" \
    -H 'Content-Type: application/json' \
    -d "[{\"signal_id\":\"$sig\",\"value\":$VAL,\"timestamp\":\"$TS\",\"quality\":192}]" > /dev/null
  echo "SEEDED: $sig = $VAL @ $TS"
done

echo ""
echo "=== Verify TDengine ==="
docker exec plantos-tdengine taos -s "use plantos_ts; select last(*) from d_comp01_motor_current;" 2>&1 | tail -3

echo DONE
