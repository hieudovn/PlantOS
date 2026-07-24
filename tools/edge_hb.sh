#!/bin/bash
echo "=== EDGE STATUS ==="
docker logs plantos-edge-v2 --tail 15 2>&1 | grep -E 'heartbeat|login|JWT|error|failed'

echo ""
echo "=== BACKEND HEARTBEAT ==="
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login -H 'Content-Type: application/json' -d '{"username":"admin","password":"PlantOS@2026!"}' | python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token',''))")
echo "Heartbeat endpoint:"
curl -s -X POST "http://localhost:8000/api/v1/edge-nodes/heartbeat" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"edge_node_id":"EDGEV2-PC-01","status":"online","version":"2.0.0"}' | head -c 200
echo ""

echo "=== EDGE NODES ==="
curl -s "http://localhost:8000/api/v1/edge-nodes" -H "Authorization: Bearer $TOKEN" | python3 -c "
import sys,json
nodes=json.load(sys.stdin)
for n in nodes:
    print(f'  {n.get(\"edge_node_id\")}: {n.get(\"status\")} heartbeat={n.get(\"last_heartbeat\",\"?\")}')
" 2>&1
echo DONE
