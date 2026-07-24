#!/bin/bash
echo "=== 1. EDGE V2 STATUS ==="
docker ps --format '{{.Names}} {{.Status}}' | grep edge
echo ""
echo "=== 2. EDGE LOG ==="
docker logs plantos-edge-v2 --tail 10 2>&1 | grep -E 'JWT|heart|login|error|connect|poll'
echo ""
echo "=== 3. LIVE SEEDER ==="
tail -3 /tmp/seeder.log 2>/dev/null || echo "NO_SEEDER_LOG"
ps aux | grep "live_seeder" | grep -v grep | head -1 || echo "SEEDER_NOT_RUNNING"
echo ""
echo "=== 4. BACKEND INGEST ==="
docker logs plantos-backend --tail 10 2>&1 | grep -E 'ingest|20[01]|error' | tail -5
echo ""
echo "=== 5. TDENGINE ==="
docker exec plantos-tdengine taos -s "use plantos_ts; select last(*) from d_comp01_motor_current;" 2>&1 | tail -3
echo ""
echo "=== 6. API DIRECT TEST ==="
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login -H 'Content-Type: application/json' -d '{"username":"admin","password":"PlantOS@2026!"}' | python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token',''))" 2>/dev/null)
if [ -z "$TOKEN" ]; then
  echo "LOGIN_FAILED"
else
  curl -s "http://localhost:8000/api/v1/measurements/history?signal_id=COMP01-MOTOR.current&from=2026-07-24T00:00&to=2026-07-24T23:59" -H "Authorization: Bearer $TOKEN" | python3 -c "
import sys,json;d=json.load(sys.stdin);data=d.get('data',[]);print(f'HISTORIAN:{len(data)} records')
if data:print(f'LATEST:{data[-1].get(\"timestamp\")} val={data[-1].get(\"value\")}')
" 2>&1
fi
echo DONE
