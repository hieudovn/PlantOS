#!/bin/bash
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login -H 'Content-Type: application/json' -d '{"username":"admin","password":"PlantOS@2026!"}' | python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token',''))")

echo "=== SIGNAL NAMES IN DB ==="
docker exec plantos-postgres psql -U plantos -d plantos -c "SELECT id, external_id, name, data_type FROM signals LIMIT 10;" 2>&1

echo "=== SEARCH FOR MOTOR CURRENT ==="
docker exec plantos-postgres psql -U plantos -d plantos -c "SELECT id, external_id, name FROM signals WHERE name LIKE '%motor%' OR external_id LIKE '%motor%' LIMIT 5;" 2>&1

echo "=== TD TABLES WITH MOTOR ==="
docker exec plantos-tdengine taos -s "use plantos_ts; show tables;" 2>&1 | grep motor

echo "=== TRY WITH SIGNAL UUID ==="
curl -s "http://localhost:8000/api/v1/signals?limit=3" -H "Authorization: Bearer $TOKEN" | python3 -c "
import sys,json
signals=json.load(sys.stdin)
for s in signals[:3]:
    sid=s.get('id','?')
    print(f'Testing signal: {sid}')
    import subprocess,json as j
" 2>&1

# Actually let's just query history with the first signal's UUID
SIG_ID=$(curl -s "http://localhost:8000/api/v1/signals?limit=1" -H "Authorization: Bearer $TOKEN" | python3 -c "import sys,json; print(json.load(sys.stdin)[0]['id'])")
echo "SIG_ID=$SIG_ID"
curl -s "http://localhost:8000/api/v1/measurements/history?signal_id=$SIG_ID&from=2026-07-20T00:00&to=2026-07-23T23:59" -H "Authorization: Bearer $TOKEN" | python3 -c "
import sys,json
d=json.load(sys.stdin)
data=d.get('data',d.get('measurements',[]))
print(f'SIG_ID history: {len(data)} records')
if data: print(f'  {data[0]}')
" 2>&1

echo DONE
