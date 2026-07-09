#!/bin/bash
# E2V2-12 Phase 1: Pre-Switch Verification
export PLANTOS_CENTER_PASSWORD='PlantOS@2026!'

echo "=== E2V2-12 PHASE 1: PRE-SWITCH VERIFICATION ==="
echo "Started: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo ""

echo "--- 12.1 v1 health ---"
echo "v1: $(curl -s -o /dev/null -w '%{http_code}' http://localhost:8001)"

echo ""
echo "--- 12.2 v2 health ---"
python3 -c "
import httpx,json
r=httpx.get('http://localhost:8011/api/status',timeout=10)
s=json.loads(r.text)
print(f'status: {s.get(\"status\")}')
print(f'edge_node: {s.get(\"edge_node_id\")}')
print(f'uptime: {s.get(\"uptime_seconds\",\"?\")}s')
bl=s.get('sync',{}).get('backlog','?')
br=s.get('buffer',{}).get('row_count','?')
print(f'backlog: {bl}  buffer_rows: {br}')
conns=s.get('connectors',{}).get('list',[])
for c in conns:
    print(f'  connector: {c[\"connector_id\"]} status={c.get(\"status\")} connected={c.get(\"connected\")}')
"

echo ""
echo "--- 12.3 Center health ---"
echo "Center: $(curl -s -o /dev/null -w '%{http_code}' http://localhost:8000/health)"

echo ""
echo "--- 12.4 Heartbeat check ---"
docker logs plantos-edge-v2 2>&1 | grep heartbeat | tail -3

echo ""
echo "--- 12.5 Ingest check ---"
docker logs plantos-edge-v2 2>&1 | grep "Flushed\|ingest\|ingest" | tail -3

echo ""
echo "--- 12.6 Baseline ---"
echo "=== BASELINE $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
python3 -c "
import httpx,json
r=httpx.get('http://localhost:8011/api/status',timeout=10)
s=json.loads(r.text)
print(f'status: {s.get(\"status\")}')
print(f'backlog: {s.get(\"sync\",{}).get(\"backlog\",\"?\")}')
print(f'buffer_rows: {s.get(\"buffer\",{}).get(\"row_count\",\"?\")}')
print(f'uptime: {s.get(\"uptime_seconds\",\"?\")}s')
"
echo ""
echo "=== PRE-SWITCH VERIFICATION COMPLETE ==="
