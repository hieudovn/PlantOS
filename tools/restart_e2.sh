#!/bin/bash
set -e
cd /opt/plantos/deployment
set -a; source .env 2>/dev/null; set +a

docker stop plantos-edge-v2 2>/dev/null || true
docker rm plantos-edge-v2 2>/dev/null || true

docker run -d \
  --name plantos-edge-v2 \
  --network deployment_plantos-net \
  -p 127.0.0.1:8011:8011 \
  -e EDGE_CONFIG_PATH=/app/agent/config/config.edge-v2.yaml \
  -e EDGE_SESSION_SECRET="${EDGE_SESSION_SECRET}" \
  -e EDGE_CENTER_PASSWORD="${EDGE_CENTER_PASSWORD}" \
  -e EDGE_API_KEY="${EDGE_API_KEY}" \
  -e CENTER_URL="${CENTER_URL}" \
  -v /tmp/edge_config.yaml:/app/agent/config/config.edge-v2.yaml:ro \
  --restart unless-stopped \
  --entrypoint /bin/sh \
  plantos-edge-v2:patched \
  -c 'pip install asyncua -q 2>/dev/null; python3 -m agent.main'

echo "Started. Waiting 15s..."
sleep 15
echo "=== LOGS ==="
docker logs plantos-edge-v2 --tail 25 2>&1
echo "=== CONNECTORS ==="
curl -s http://localhost:8011/api/status 2>&1 | python3 -c "
import sys, json
d = json.load(sys.stdin)
print(f'Buffer: {d[\"buffer\"][\"row_count\"]} rows')
for c in d['connectors']['list']:
    print(f'{c[\"connector_id\"]}: {c[\"status\"]} connected={c[\"connected\"]} signals={c[\"signal_count\"]} error={c[\"last_error\"]}')
" 2>&1
