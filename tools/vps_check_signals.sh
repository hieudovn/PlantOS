#!/bin/bash
set -e
cd /opt/plantos

RESP=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"PlantOS@2026!"}')
TOKEN=$(echo "$RESP" | python3 -c "import sys,json;print(json.load(sys.stdin).get('access_token',''))")
echo "Token OK: ${TOKEN:0:10}..."

echo "=== DEMO-PLANT signals ==="
curl -s -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/signals?plant_id=DEMO-PLANT" | \
  python3 -c "
import sys,json
d=json.load(sys.stdin)
print(f'Count: {len(d)}')
for s in d[:5]:
    print(f'  {s[\"signal_id\"]}')
"

echo "=== EDGEV2-DEMO signals ==="
curl -s -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/signals?plant_id=EDGEV2-DEMO" | \
  python3 -c "
import sys,json
d=json.load(sys.stdin)
print(f'Count: {len(d)}')
for s in d[:5]:
    print(f'  {s[\"signal_id\"]}')
"
