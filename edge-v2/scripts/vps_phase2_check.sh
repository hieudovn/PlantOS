#!/bin/bash
# Phase 2: VPS pre-flight check
set -e

echo '=== Edge nodes in Center ==='
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"PlantOS@2026"}' | \
  python3 -c 'import sys,json; print(json.load(sys.stdin).get("access_token",""))')
echo "Token obtained: ${TOKEN:0:20}..."
curl -s -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/edge-nodes | \
  python3 -c '
import sys,json
nodes=json.load(sys.stdin)
for n in nodes:
    print("  {}: {}".format(n.get("edge_node_id","?"), n.get("status","?")))
'

echo ''
echo '=== v2 status ==='
curl -s http://localhost:8011/api/status | \
  python3 -c '
import sys,json
d=json.load(sys.stdin)
print("rows={}, backlog={}".format(d.get("buffer",{}).get("row_count",0), d.get("sync",{}).get("backlog",0)))
'

echo ''
echo '=== v2 recent measurements ==='
curl -s http://localhost:8011/api/measurements/latest?limit=5

echo ''
echo '=== v1 data check ==='
curl -s -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/measurements/history?plant_id=DEMO-PLANT&limit=5" | \
  python3 -c '
import sys,json
d=json.load(sys.stdin)
if isinstance(d,list):
    print("v1 points: {}".format(len(d)))
elif isinstance(d,dict):
    print("v1 points: {}".format(len(d.get("measurements",[]))))
else:
    print("v1: unexpected format")
' 2>/dev/null || echo "v1 API check done"
