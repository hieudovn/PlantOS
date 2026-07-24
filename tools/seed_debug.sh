#!/bin/bash
echo "=== SEEDER LOG ==="
cat /tmp/live_seeder.log 2>&1 | head -5

echo "=== PYTHON REQUESTS ==="
python3 -c "import requests; print('REQUESTS_OK')" 2>&1 || echo "NO_REQUESTS"

echo "=== TEST INGEST ==="
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login -H 'Content-Type: application/json' -d '{"username":"admin","password":"PlantOS@2026!"}' | python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token',''))")
curl -sv -X POST http://localhost:8000/api/v1/measurements/ingest \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '[{"signal_id":"COMP01-MOTOR.current","value":42.5,"timestamp":"2026-07-23T08:20:00Z","quality":192}]' 2>&1 | tail -5
echo DONE
