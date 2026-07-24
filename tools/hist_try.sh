#!/bin/bash
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login -H 'Content-Type: application/json' -d '{"username":"admin","password":"PlantOS@2026!"}' | python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token',''))")

echo "=== TRY motor_101.motor_current ==="
curl -s "http://localhost:8000/api/v1/measurements/history?signal_id=motor_101.motor_current&from=2026-07-20T00:00&to=2026-07-23T23:59" -H "Authorization: Bearer $TOKEN" | python3 -c "
import sys,json
d=json.load(sys.stdin)
data=d.get('data',[])
print(f'RECORDS: {len(data)}')
if data: print(f'SAMPLE: {data[0]}')
" 2>&1

echo "=== TRY d_motor_101_motor_current (strip d_) ==="
curl -s "http://localhost:8000/api/v1/measurements/history?signal_id=motor_101_motor_current&from=2026-07-20T00:00&to=2026-07-23T23:59" -H "Authorization: Bearer $TOKEN" | python3 -c "
import sys,json
d=json.load(sys.stdin)
data=d.get('data',[])
print(f'RECORDS: {len(data)}')
if data: print(f'SAMPLE: {str(data[0])[:150]}')
" 2>&1

echo DONE
