#!/bin/bash
# E2V2-13: Check current state
echo "=== v1 ==="
curl -s -o /dev/null -w '%{http_code}' http://localhost:8001

echo ""
echo "=== v2 ==="
python3 -c "
import httpx,json
d=json.loads(httpx.get('http://localhost:8011/api/status',timeout=5).text)
print(f'status={d[\"status\"]} bl={d[\"sync\"][\"backlog\"]} buf={d[\"buffer\"][\"row_count\"]}')
for c in d['connectors']['list']:
    print(f'  {c[\"connector_id\"]}: sig={c[\"signal_count\"]} {c[\"status\"]} conn={c[\"connected\"]}')
"

echo ""
echo "=== Simulator ==="
if [ -f /tmp/http_simulator.py ]; then
    head -5 /tmp/http_simulator.py
else
    echo "No simulator file found"
fi

SIG_COUNT=$(curl -s http://localhost:9998/ 2>/dev/null | python3 -c "import sys,json;d=json.load(sys.stdin);print(len(d))" 2>/dev/null)
echo "Simulator signals: $SIG_COUNT"

echo ""
echo "=== Center ==="
curl -s -o /dev/null -w '%{http_code}' http://localhost:8000/health
echo ""

echo "=== Config ==="
docker exec plantos-edge-v2 cat /app/agent/config/config.edge-v2.yaml 2>/dev/null | head -30 || echo "Cannot read config"
