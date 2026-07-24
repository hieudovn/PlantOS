#!/bin/bash
set -e
cd /opt/plantos
git fetch origin phase8-closure 2>/dev/null
git checkout -f --detach 801e952 2>/dev/null || true
echo "CHECKOUT: $(git rev-parse --short=7 HEAD)"

docker build -t plantos-backend:801e952 -f backend/Dockerfile backend 2>&1 | tail -3

docker stop plantos-backend 2>/dev/null; docker rm plantos-backend 2>/dev/null
docker run -d --name plantos-backend --network deployment_plantos-net -p 127.0.0.1:8000:8000 \
  -e JWT_SECRET=1d7a647e277b94094cbbc0ea01b3571c361a3d46313edd6a442ae317595159bf \
  -e API_KEYS=d1048800025cfbc2187d6a49a9c482f8cff91f63e70ac41a \
  -e POSTGRES_HOST=postgres -e POSTGRES_PORT=5432 -e POSTGRES_DB=plantos -e POSTGRES_USER=plantos \
  -e POSTGRES_PASSWORD=plantos_test \
  -e TDENGINE_HOST=tdengine -e TDENGINE_PORT=6041 -e TDENGINE_DATABASE=plantos_ts \
  -e TDENGINE_USER=root -e TDENGINE_PASSWORD=taosdata \
  -e EMQX_HOST=emqx -e EMQX_MQTT_PORT=1883 \
  plantos-backend:801e952
sleep 8

TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login -H 'Content-Type: application/json' -d '{"username":"admin","password":"PlantOS@2026!"}' | python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token',''))")

echo "=== SAFE NAME TEST ==="
docker exec plantos-backend python3 -c "
import sys; sys.path.insert(0,'/app')
from app.modules.historian.tdengine_adapter import TDengineHistorianAdapter
a=TDengineHistorianAdapter()
for t in ['COMP-01.motor_current','PUMP-101.flow_rate']:
    print(f'{t} -> d_{a._safe_name(t)}')
" 2>&1

echo "=== HISTORIAN ==="
curl -s "http://localhost:8000/api/v1/measurements/history?signal_id=COMP-01.motor_current&from=2026-07-01T00:00&to=2026-07-23T23:59" -H "Authorization: Bearer $TOKEN" | python3 -c "
import sys,json
d=json.load(sys.stdin)
data=d.get('data',[])
print(f'RECORDS: {len(data)}')
if data: print(str(data[0])[:150])
" 2>&1

echo DONE
