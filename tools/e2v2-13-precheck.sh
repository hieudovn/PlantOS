#!/bin/bash
# E2V2-13: Pre-check — check what signals have actual measurement data

echo "=== Simulator (port 9998) ==="
curl -s http://localhost:9998/ | python3 -m json.tool 2>/dev/null | head -30

echo ""
echo "=== v1 Edge (port 8001) sample data ==="
curl -s http://localhost:8001/api/v1/data 2>/dev/null | python3 -c "
import sys, json
d = json.load(sys.stdin)
if isinstance(d, dict):
    keys = list(d.keys())
    print(f'Top-level keys ({len(keys)}): {keys[:15]}')
    for k in keys[:3]:
        v = d[k]
        if isinstance(v, list):
            print(f'  {k}: [{len(v)} items] {v[0] if v else \"empty\"}')
        else:
            print(f'  {k}: {v}')
elif isinstance(d, list):
    print(f'List of {len(d)} items')
    print(json.dumps(d[:3], indent=2))
" 2>/dev/null || echo "v1 API not reachable"

echo ""
echo "=== v2 Connector Config ==="
cat /opt/plantos/edge-v2/agent/config/config.edge-v2.yaml | head -80

echo ""
echo "=== v2 buffer sample (latest 2 rows) ==="
curl -s http://localhost:8011/api/status | python3 -m json.tool
