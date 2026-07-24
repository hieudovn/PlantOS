#!/bin/bash
set -e

echo "=== Build + Deploy ==="
cd /opt/plantos
git fetch origin phase8-closure 2>/dev/null
git checkout -f --detach 82b1605 2>/dev/null || true
echo "CHECKOUT: $(git rev-parse --short=7 HEAD)"

docker build -t plantos-backend:82b1605 -f backend/Dockerfile backend 2>&1 | tail -3

docker stop plantos-backend 2>/dev/null; docker rm plantos-backend 2>/dev/null
docker run -d --name plantos-backend --network deployment_plantos-net -p 127.0.0.1:8000:8000 \
  -e JWT_SECRET=1d7a647e277b94094cbbc0ea01b3571c361a3d46313edd6a442ae317595159bf \
  -e API_KEYS=d1048800025cfbc2187d6a49a9c482f8cff91f63e70ac41a \
  -e POSTGRES_HOST=postgres -e POSTGRES_PORT=5432 -e POSTGRES_DB=plantos -e POSTGRES_USER=plantos \
  -e POSTGRES_PASSWORD=plantos_test \
  -e TDENGINE_HOST=tdengine -e TDENGINE_PORT=6041 -e TDENGINE_DATABASE=plantos_ts \
  -e TDENGINE_USER=root -e TDENGINE_PASSWORD=taosdata \
  -e EMQX_HOST=emqx -e EMQX_MQTT_PORT=1883 \
  plantos-backend:82b1605
sleep 8

echo "=== Login ==="
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login -H 'Content-Type: application/json' -d '{"username":"admin","password":"PlantOS@2026!"}' | python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token',''))")
echo "TOKEN: ${TOKEN:0:20}..."

echo "=== Historian ==="
curl -s "http://localhost:8000/api/v1/measurements/history?signal_id=COMP-01.motor_current&from=2026-07-20T00:00&to=2026-07-23T23:59" -H "Authorization: Bearer $TOKEN" | python3 -c "
import sys,json
d=json.load(sys.stdin)
data=d.get('data',d.get('measurements',[]))
print(f'HISTORIAN: {len(data)} records')
if data: print(f'  SAMPLE: {data[0]}')
" 2>&1

echo "=== Edge Heartbeat ==="
curl -s -X POST "http://localhost:8000/api/v1/edge-nodes/heartbeat" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"edge_node_id":"EDGEV2-PC-01","status":"online","version":"2.0.0","hostname":"edge-v2","ip_address":"172.19.0.7"}' | head -c 200
echo ""

echo "=== Edge Status ==="
curl -s "http://localhost:8000/api/v1/edge-nodes" -H "Authorization: Bearer $TOKEN" | python3 -c "
import sys,json
for n in json.load(sys.stdin):
    print(f'  {n.get(\"edge_node_id\",\"?\")}: {n.get(\"status\",\"?\")}')
" 2>&1

echo DONE
