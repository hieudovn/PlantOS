#!/bin/bash
set -e
echo "=== Step 1: Copy config to correct path ==="
docker exec plantos-edge-v2 cp /app/agent/config/config.edge-v2.yaml /app/edge-v2/agent/config/config.edge-v2.yaml
echo "OK"

echo "=== Step 2: Verify config ==="
python3 -c "
import yaml
with open('/app/edge-v2/agent/config/config.edge-v2.yaml') as f:
    c = yaml.safe_load(f)
wtp = c['connectors']['mirror_wtp_signals']
print(f'tags={len(wtp[\"tags\"])} url={wtp[\"connection\"][\"url\"]}')
"

echo "=== Step 3: Restart v2 ==="
docker restart plantos-edge-v2
sleep 15

echo "=== Step 4: Verify 19 signals ==="
python3 -c "
import httpx, json
r = httpx.get('http://localhost:8011/api/status', timeout=10)
d = json.loads(r.text)
print(f'status={d[\"status\"]}')
for c in d['connectors']['list']:
    print(f'  {c[\"connector_id\"]}: sig={c[\"signal_count\"]} {c[\"status\"]} conn={c[\"connected\"]}')
"

echo "=== v1 ==="
curl -s -o /dev/null -w '%{http_code}' http://localhost:8001
echo ""
