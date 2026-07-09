#!/bin/bash
set -e

echo "=== v2 Container ==="
docker ps --filter name=plantos-edge-v2

echo ""
echo "=== v2 Status ==="
curl -s http://localhost:8011/api/status | python3 -c "
import sys,json
d=json.load(sys.stdin)
b=d.get('buffer',{})
s=d.get('sync',{})
print(f'rows={b.get(\"row_count\",0)} backlog={s.get(\"backlog\",0)}')
"

echo ""
echo "=== v2 Logs (last 5) ==="
docker logs plantos-edge-v2 2>&1 | tail -5

echo ""
echo "=== Side-by-Side Comparison ==="
export PLANTOS_CENTER_PASSWORD='PlantOS@2026!'
cd /home/plantos
python3 tools/compare_v1_v2_data.py --hours 0.5 --center-url http://localhost:8000 2>&1 | tail -25

echo ""
echo "=== Secret Scan ==="
grep -rn 'PlantOS@2026' /home/plantos/edge-v2/agent/config/ 2>/dev/null && echo "FOUND HARDCODED" || echo "CLEAN: no hardcoded passwords"
grep session_secret /home/plantos/edge-v2/agent/config/config.edge-v2.yaml

echo ""
echo "=== DONE ==="
