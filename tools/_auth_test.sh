#!/bin/bash
# Test Center API with JWT auth
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"PlantOS@2026!"}' | \
  python3 -c "import sys,json;print(json.load(sys.stdin).get('access_token',''))")

echo "Token: ${TOKEN:0:20}..."

echo ""
echo "=== Plants ==="
curl -s -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/plants | python3 -c "
import sys,json
d=json.load(sys.stdin)
if isinstance(d,list):
    for p in d: print(' ',p.get('plant_id','?'))
else:
    print(type(d).__name__, list(d.keys())[:5])
"

echo ""
echo "=== Edge Nodes ==="
curl -s -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/edge-nodes | python3 -c "
import sys,json
d=json.load(sys.stdin)
if isinstance(d,list):
    for n in d: print(' ',n.get('edge_node_id','?'), n.get('status','?'))
else:
    print(d[:200])
"

echo ""
echo "=== Measurements (DEMO-PLANT, last 2) ==="
curl -s -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/measurements/history?plant_id=DEMO-PLANT&limit=2" | python3 -c "
import sys,json
d=json.load(sys.stdin)
if isinstance(d,list):
    print(len(d),'measurements')
    for m in d[:2]: print(' ',m.get('signal_id','?'), m.get('value','?'))
elif isinstance(d,dict):
    ms=d.get('measurements',d.get('data',[]))
    print(len(ms),'measurements')
    for m in ms[:2]: print(' ',m)
else:
    print(str(d)[:200])
"

echo ""
echo "=== Heartbeat test (JWT) ==="
curl -s -w "\nHTTP:%{http_code}" -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -X POST http://localhost:8000/api/v1/edge-nodes/heartbeat \
  -d '{"edge_node_id":"EDGEV2-PC-01","status":"online"}'

echo ""
echo "=== DONE ==="
