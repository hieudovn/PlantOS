#!/bin/bash
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login -H 'Content-Type: application/json' -d '{"username":"admin","password":"PlantOS@2026!"}' | python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token',''))")

echo "=== API RESPONSE FORMAT ==="
curl -s "http://localhost:8000/api/v1/measurements/history?signal_id=COMP01-MOTOR.current&from=2026-07-23T08:00&to=2026-07-23T09:00" \
  -H "Authorization: Bearer $TOKEN" | python3 -c "
import sys,json
d=json.load(sys.stdin)
data=d.get('data',[])[:2]
for item in data:
    print(item)
" 2>&1

echo ""
echo "=== TIMESTAMP FORMAT ==="
curl -s "http://localhost:8000/api/v1/measurements/history?signal_id=COMP01-MOTOR.current&from=2026-07-23T08:00&to=2026-07-23T09:00" \
  -H "Authorization: Bearer $TOKEN" | python3 -c "
import sys,json
d=json.load(sys.stdin)
data=d.get('data',[])
for item in data[:3]:
    ts=item.get('timestamp','?')
    print(f'timestamp: {ts} type: {type(ts).__name__}')
" 2>&1
echo DONE
