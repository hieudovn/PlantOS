#!/bin/bash
set -e
echo "=== Backup old config ==="
cp /home/plantos/edge-v2/agent/config/config.edge-v2.yaml /home/plantos/edge-v2/agent/config/config.edge-v2.yaml.bak
echo "=== Copy 19-tag config from container ==="
docker cp plantos-edge-v2:/app/agent/config/config.edge-v2.yaml /tmp/new_config.yaml
cp /tmp/new_config.yaml /home/plantos/edge-v2/agent/config/config.edge-v2.yaml
echo "=== Verify host config ==="
python3 -c "
import yaml
with open('/home/plantos/edge-v2/agent/config/config.edge-v2.yaml') as f:
    c = yaml.safe_load(f)
wtp = c['connectors']['mirror_wtp_signals']
print('tags=' + str(len(wtp['tags'])))
"
echo "=== Restart v2 ==="
docker restart plantos-edge-v2
sleep 15
echo "=== Verify connectors ==="
python3 -c "
import httpx, json
r = httpx.get('http://localhost:8011/api/status', timeout=10)
d = json.loads(r.text)
for c in d['connectors']['list']:
    print(f\"  {c['connector_id']}: sig={c['signal_count']}\")
"
echo "=== v1 ==="
curl -s -o /dev/null -w '%{http_code}' http://localhost:8001
echo ""
