#!/bin/bash
set -e
echo "Creating directory..."
docker exec plantos-edge-v2 mkdir -p /app/edge-v2/agent/config
echo "Copying config..."
docker exec plantos-edge-v2 cp /app/agent/config/config.edge-v2.yaml /app/edge-v2/agent/config/config.edge-v2.yaml
echo "Verifying..."
docker exec plantos-edge-v2 python3 -c "import yaml;f=open('/app/edge-v2/agent/config/config.edge-v2.yaml');c=yaml.safe_load(f);wtp=c['connectors']['mirror_wtp_signals'];print('tags='+str(len(wtp['tags'])))"
echo "Restarting..."
docker restart plantos-edge-v2
sleep 15
echo "Verifying connector..."
docker exec plantos-edge-v2 python3 -c "
import httpx, json
r = httpx.get('http://localhost:8011/api/status', timeout=10)
d = json.loads(r.text)
for c in d['connectors']['list']:
    print(f\"  {c['connector_id']}: sig={c['signal_count']} {c['status']}\")
"
echo "v1: $(curl -s -o /dev/null -w '%{http_code}' http://localhost:8001)"
