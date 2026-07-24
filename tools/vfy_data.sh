#!/bin/bash
cat /tmp/seeder.log 2>&1 | head -5
echo "==="
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login -H 'Content-Type: application/json' -d '{"username":"admin","password":"PlantOS@2026!"}' | python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token',''))")
curl -s 'http://localhost:8000/api/v1/measurements/history?signal_id=COMP01-MOTOR.current&from=2026-07-23T16:00:00%2B07:00&to=2026-07-23T18:00:00%2B07:00' -H "Authorization: Bearer $TOKEN" | python3 -c "
import sys,json
d=json.load(sys.stdin)
data=d.get('data',[])
print(f'TOTAL: {len(data)}')
for p in data[-5:]:
    print(f'  {p[\"timestamp\"]} = {p[\"value\"]}')
"
echo DONE
