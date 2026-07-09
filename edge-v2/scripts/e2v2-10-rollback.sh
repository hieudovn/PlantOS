#!/bin/bash
set -e

echo "=== E2V2-10 TASK 4: ROLLBACK ==="
echo "Started: $(date -u +%Y-%m-%dT%H:%M:%SZ)"

RECOVERY_START=$(date +%s)

# Step 1: Stop Edge v2
echo ""
echo "Stopping v2..."
docker compose -f /opt/plantos/deployment/docker-compose.yml stop plantos-edge-v2

# Step 2: Verify Edge v1 still running
echo "v1 after v2 stop: $(curl -s -o /dev/null -w '%{http_code}' http://localhost:8001)"

# Step 3: Verify v1 heartbeat
sleep 5
echo ""
echo "Edge nodes after v2 stop:"
python3 -c "
import httpx, json
resp = httpx.get('http://localhost:8000/api/v1/edge-nodes', timeout=10)
for n in resp.json():
    print(f'  {n[\"edge_node_id\"]}: {n.get(\"status\",\"?\")}')
"

# Step 4: Verify v1 data flow
echo ""
echo "v1 measurements after rollback:"
python3 -c "
import httpx, json
resp = httpx.get('http://localhost:8000/api/v1/measurements/history?plant_id=DEMO-PLANT&limit=3', timeout=10)
d = resp.json()
print(f'  {len(d)} points')
"

RECOVERY_END=$(date +%s)
echo "Recovery time: $((RECOVERY_END - RECOVERY_START)) seconds"

# Step 5: Restore v2 to mirror mode
echo ""
echo "Restarting v2 in mirror mode..."
docker compose -f /opt/plantos/deployment/docker-compose.yml start plantos-edge-v2
sleep 10

echo ""
echo "v2 after restart: $(python3 -c "
import httpx, json
resp = httpx.get('http://localhost:8011/api/status', timeout=10)
print(json.loads(resp.text).get('status','?'))
")"

# Final state
echo ""
echo "=== FINAL STATE ==="
echo "v1: $(curl -s -o /dev/null -w '%{http_code}' http://localhost:8001)"
echo "v2: $(python3 -c "
import httpx, json
resp = httpx.get('http://localhost:8011/api/status', timeout=10)
print(json.loads(resp.text).get('status','?'))
")"
echo "Center: $(curl -s -o /dev/null -w '%{http_code}' http://localhost:8000/health)"

# Check backlog
BACKLOG=$(python3 -c "
import httpx, json
resp = httpx.get('http://localhost:8011/api/status', timeout=10)
s = json.loads(resp.text)
print(s.get('sync',{}).get('backlog','?'))
" 2>/dev/null || echo "?")
echo "v2 backlog: $BACKLOG"

echo ""
echo "=== DRY-RUN COMPLETE ==="
echo "Finished: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
