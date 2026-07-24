#!/bin/bash
# Fix edge center_url to use IP instead of hostname
python3 -c "
d = open('/opt/plantos/edge-v2/agent/config/config.edge-v2.yaml', 'r').read()
d = d.replace('center_url: http://backend:8000', 'center_url: http://172.19.0.1:8000')
if '172.19.0.1:8000' in d:
    open('/opt/plantos/edge-v2/agent/config/config.edge-v2.yaml', 'w').write(d)
    print('CENTER_URL_FIXED_TO_IP')
else:
    # Try localhost variant
    d = d.replace('center_url: http://localhost:8000', 'center_url: http://172.19.0.1:8000')
    open('/opt/plantos/edge-v2/agent/config/config.edge-v2.yaml', 'w').write(d)
    print('CENTER_URL_FIXED')
"

docker restart plantos-edge-v2
sleep 10

echo "=== EDGE LOG ==="
docker logs plantos-edge-v2 --tail 10 2>&1 | grep -E 'JWT|login|heart|ingest|error'

echo "=== MEASUREMENT AFTER RESTART ==="
sleep 5
docker logs plantos-backend --tail 5 2>&1 | grep -E 'ingest|20[01]'

echo DONE
