#!/bin/bash
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login -H 'Content-Type: application/json' -d '{"username":"admin","password":"PlantOS@2026!"}' | python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token',''))")

echo "=== SIGNAL DETAILS ==="
curl -s "http://localhost:8000/api/v1/signals?limit=3" -H "Authorization: Bearer $TOKEN" | python3 -c "
import sys,json
signals = json.load(sys.stdin)
for s in signals[:5]:
    print(json.dumps({k:s[k] for k in ['id','name','external_id','data_type'] if k in s}, default=str))
" 2>&1

echo "=== TDENGINE TABLES SAMPLE ==="
docker exec plantos-tdengine taos -s 'use plantos_ts; show tables;' 2>&1 | grep 'd_comp' | head -5

echo "=== TRY WITH TD TABLE NAME ==="
curl -s "http://localhost:8000/api/v1/measurements/history?signal_id=d_comp01_motor_current&from=2026-07-20T00:00&to=2026-07-23T23:59" \
  -H "Authorization: Bearer $TOKEN" | python3 -c "
import sys,json
d=json.load(sys.stdin)
data=d.get('data',[])
print(f'data: {len(data)} items')
" 2>&1

echo DONE
