#!/bin/bash
set -e

echo "=== Generating Edge V2 config from contract ==="
# Fix path in generator
sed -i 's|/opt/plantos/examples/vf-plantos-contract.yaml|/tmp/vf-plantos-contract.yaml|' /tmp/gen_edge2_config.py
python3 /tmp/gen_edge2_config.py

echo ""
echo "=== Restarting Edge V2 with new config ==="
docker stop plantos-edge-v2 2>/dev/null || true
docker rm plantos-edge-v2 2>/dev/null || true

# Read env vars from .env
set -a; source /opt/plantos/deployment/.env 2>/dev/null; set +a

docker run -d \
  --name plantos-edge-v2 \
  --network deployment_plantos-net \
  -p 127.0.0.1:8011:8011 \
  -e EDGE_CONFIG_PATH=/app/agent/config/config.edge-v2.yaml \
  -e EDGE_SESSION_SECRET="$EDGE_SESSION_SECRET" \
  -e EDGE_CENTER_PASSWORD="$EDGE_CENTER_PASSWORD" \
  -e EDGE_API_KEY="$EDGE_API_KEY" \
  -e CENTER_URL="$CENTER_URL" \
  -v /tmp/edge_config.yaml:/app/agent/config/config.edge-v2.yaml:ro \
  --restart unless-stopped \
  plantos-edge-v2:patched

echo ""
echo "Waiting 10 seconds..."
sleep 10

echo "=== EDGE V2 STATUS ==="
docker ps --filter name=plantos-edge-v2 --format '{{.Names}} {{.Status}}'

echo ""
echo "=== EDGE V2 LOGS ==="
docker logs plantos-edge-v2 --tail 20 2>&1

echo ""
echo "=== CONNECTORS ==="
curl -s http://localhost:8011/api/status | python3 -c "
import sys, json
d = json.load(sys.stdin)
print(f'Buffer: {d[\"buffer\"][\"row_count\"]} rows')
for c in d['connectors']['list']:
    print(f'{c[\"connector_id\"]}: {c[\"status\"]} connected={c[\"connected\"]} signals={c[\"signal_count\"]} error={c[\"last_error\"]}')
"
