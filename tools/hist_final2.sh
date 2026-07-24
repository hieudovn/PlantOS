#!/bin/bash
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login -H 'Content-Type: application/json' -d '{"username":"admin","password":"PlantOS@2026!"}' | python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token',''))")

echo "=== SIGNALS TABLE ==="
docker exec plantos-postgres psql -U plantos -d plantos -c "SELECT id, name, external_id FROM signals LIMIT 10;" 2>&1

echo "=== TDENGINE MOTOR TABLES ==="
docker exec plantos-tdengine taos -s "use plantos_ts; show tables;" 2>&1 | grep motor

echo "=== TRY UUID SIGNAL ==="
SIG=$(curl -s "http://localhost:8000/api/v1/signals?limit=1" -H "Authorization: Bearer $TOKEN" | python3 -c "import sys,json; print(json.load(sys.stdin)[0]['id'])")
curl -s "http://localhost:8000/api/v1/measurements/history?signal_id=$SIG&from=2026-07-20T00:00&to=2026-07-23T23:59" -H "Authorization: Bearer $TOKEN" | python3 -c "
import sys,json
d=json.load(sys.stdin)
print(f'keys: {list(d.keys())}')
data=d.get('data',[])
print(f'data: {len(data)}')
" 2>&1
echo DONE
