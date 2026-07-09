#!/bin/bash
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"PlantOS@2026!"}' | \
  python3 -c "import sys,json;print(json.load(sys.stdin).get('access_token',''))")
echo "Token: ${TOKEN:0:20}"

echo "=== Signals for EDGEV2-DEMO ==="
curl -s -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/signals?plant_id=EDGEV2-DEMO" | \
  python3 -c "
import sys,json
d=json.load(sys.stdin)
print(f'{len(d)} signals')
for s in d[:3]: print(' ',s.get('signal_id','?'))
"

echo ""
echo "=== Measurement test (EDGEV2-DEMO) ==="
FROM=$(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S)
TO=$(date -u +%Y-%m-%dT%H:%M:%S)
curl -s -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/measurements/history?signal_id=PUMP-101.flow_rate&from=${FROM}&to=${TO}" | \
  python3 -c "
import sys,json
d=json.load(sys.stdin)
if isinstance(d,dict):
    pts=d.get('data',[])
    print(f'{len(pts)} points')
    for p in pts[:3]: print(' ',p.get('value','?'))
else:
    print(str(d)[:200])
"
echo "DONE"
