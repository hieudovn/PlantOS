#!/bin/bash
# Revert center_url to Docker DNS name
python3 -c "
d = open('/opt/plantos/edge-v2/agent/config/config.edge-v2.yaml', 'r').read()
d = d.replace('center_url: http://172.19.0.1:8000', 'center_url: http://plantos-backend:8000')
open('/opt/plantos/edge-v2/agent/config/config.edge-v2.yaml', 'w').write(d)
print('CENTER_URL -> plantos-backend')
"

# Also check what hostnames the edge can resolve
echo "=== DNS CHECK ==="
docker exec plantos-edge-v2 getent hosts plantos-backend 2>&1 || echo "no plantos-backend"
docker exec plantos-edge-v2 getent hosts backend 2>&1 || echo "no backend"

docker restart plantos-edge-v2
sleep 12

echo "=== EDGE LOG ==="
docker logs plantos-edge-v2 2>&1 | grep -E 'JWT login|heart|ingest|success|failed' | tail -5

echo "=== BACKEND INGEST ==="
docker logs plantos-backend --tail 3 2>&1 | grep -E 'ingest|20[01]'
echo DONE
