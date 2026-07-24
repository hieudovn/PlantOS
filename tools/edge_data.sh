#!/bin/bash
echo "=== EDGE V2 STATUS ==="
docker logs plantos-edge-v2 --tail 20 2>&1 | grep -E 'ingest|measurement|poll|connector|heart|JWT|error|HTTP'

echo ""
echo "=== BACKEND INGEST LOGS ==="
docker logs plantos-backend --tail 20 2>&1 | grep -E 'ingest|200|201'

echo ""
echo "=== TDENGINE LATEST DATA ==="
docker exec plantos-tdengine taos -s "use plantos_ts; select last(*) from d_comp01_motor_current;" 2>&1 | tail -3

echo ""
echo "=== EDGE BUFFER ==="
curl -s http://localhost:8011/api/status | python3 -c "import sys,json; d=json.load(sys.stdin); b=d.get('buffer',{}); print(f'Buffer: {b.get(\"row_count\",0)} rows, {b.get(\"size_bytes\",0)} bytes')" 2>&1

echo DONE
