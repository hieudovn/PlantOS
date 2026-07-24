#!/bin/bash
echo "=== VN LOCAL TIME ==="
TZ='Asia/Ho_Chi_Minh' date
echo "=== UTC TIME ==="
date -u

echo ""
echo "=== SIMULATOR TIMESTAMP (inside Edge V2) ==="
docker exec plantos-edge-v2 python3 /tmp/_simtest.py 2>/dev/null
if [ $? -ne 0 ]; then
  docker exec plantos-edge-v2 python3 -c 'import urllib.request, json; r = urllib.request.urlopen("http://localhost:9998/", timeout=5); d = json.loads(r.read()); print("Simulator ts:", d["timestamp"])'
fi

echo ""
echo "=== TDENGINE RAW ==="
docker exec plantos-tdengine taos -s "SELECT ts, value FROM plantos_ts.measurements WHERE signal_id = 'PUMP-101.flow_rate' ORDER BY ts DESC LIMIT 3;" 2>&1

echo ""
echo "=== BACKEND CONTAINER TZ ==="
docker exec plantos-backend python3 -c 'import time; print("Backend TZ:", time.tzname); from datetime import datetime; print("Now:", datetime.now())'

echo ""
echo "=== EDGE V2 CONTAINER TZ ==="
docker exec plantos-edge-v2 python3 -c 'import time; print("EdgeV2 TZ:", time.tzname); from datetime import datetime; print("Now:", datetime.now())'
