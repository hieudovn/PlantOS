#!/bin/bash
echo "=== CHECK STATE AFTER DRY-RUN ==="
echo "v1: $(curl -s -o /dev/null -w '%{http_code}' http://localhost:8001)"
V2_STATUS=$(curl -s http://localhost:8011/api/status 2>/dev/null | python3 -c 'import sys,json;print(json.load(sys.stdin).get("status","?"))' 2>/dev/null)
echo "v2: $V2_STATUS"
echo "Center: $(curl -s -o /dev/null -w '%{http_code}' http://localhost:8000/health)"
V2_BACKLOG=$(curl -s http://localhost:8011/api/status 2>/dev/null | python3 -c 'import sys,json;print(json.load(sys.stdin).get("sync",{}).get("backlog","?"))' 2>/dev/null)
echo "Backlog: $V2_BACKLOG"
echo ""
echo "Edge nodes:"
curl -s http://localhost:8000/api/v1/edge-nodes 2>/dev/null | python3 -c '
import sys,json
d=json.load(sys.stdin)
for n in d if isinstance(d,list) else []:
    print(f"  {n[\"edge_node_id\"]}: {n.get(\"status\",\"?\")}")
' 2>/dev/null
echo ""
echo "Comparison files:"
ls -la /tmp/dry_run_comparison_*.csv 2>/dev/null || echo "  (none found)"
