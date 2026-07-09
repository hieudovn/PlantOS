#!/bin/bash
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"PlantOS@2026!"}' | \
  python3 -c "import sys,json;print(json.load(sys.stdin).get('access_token',''))")

echo "=== Signals raw (HTTP status) ==="
curl -s -w "\nHTTP:%{http_code}" -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/signals?plant_id=EDGEV2-DEMO" | tail -3

echo ""
echo "=== Signals no filter ==="
curl -s -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/signals" | python3 -c "
import sys,json
try:
    d=json.load(sys.stdin)
    print(f'{len(d)} total signals')
    for s in d[:3]: print(' ',s.get('signal_id','?'))
except: print('PARSE ERROR')
"

echo ""
echo "=== DEMO-PLANT signals ==="
curl -s -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/signals?plant_id=DEMO-PLANT" | python3 -c "
import sys,json
try:
    d=json.load(sys.stdin)
    print(f'{len(d)} signals')
    for s in d[:3]: print(' ',s.get('signal_id','?'))
except Exception as e: print(f'ERROR: {e}')
"
echo "DONE"
