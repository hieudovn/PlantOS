#!/bin/bash
# Kill old seeder
pkill -f "live_seeder" 2>/dev/null || true

# Test correct format
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login -H 'Content-Type: application/json' -d '{"username":"admin","password":"PlantOS@2026!"}' | python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token',''))")

echo "=== TEST NEW FORMAT ==="
curl -s -X POST http://localhost:8000/api/v1/measurements/ingest \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"source":"test","measurements":[{"timestamp":"2026-07-23T08:25:00Z","signal_id":"COMP01-MOTOR.current","value":42.5,"quality":"GOOD"}]}'
echo ""

echo "=== CHECK TDENGINE ==="
sleep 2
docker exec plantos-tdengine taos -s "use plantos_ts; select last(*) from d_comp01_motor_current;" 2>&1 | tail -3

echo "=== START LIVE SEEDER ==="
cat > /tmp/live_seeder2.py << 'PYEOF'
import time, random, json, urllib.request, os
from datetime import datetime, timezone

CENTER = "http://localhost:8000"

# Login
req = urllib.request.Request(f"{CENTER}/api/v1/auth/login",
    data=json.dumps({"username":"admin","password":"PlantOS@2026!"}).encode(),
    headers={"Content-Type":"application/json"})
token = json.loads(urllib.request.urlopen(req).read())["access_token"]
print(f"SEEDER: LOGIN_OK", flush=True)

count = 0
signals = ["COMP01-MOTOR.current","COMP01-MOTOR.winding_temp","COMP01-MOTOR.motor_power","PUMP-101.flow_rate"]

while True:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    measurements = []
    for sig in signals:
        val = round(random.uniform(10, 150), 2)
        measurements.append({"timestamp": ts, "signal_id": sig, "value": val, "quality": "GOOD"})
    
    body = json.dumps({"source": "live_seeder", "measurements": measurements})
    req = urllib.request.Request(f"{CENTER}/api/v1/measurements/ingest",
        data=body.encode(),
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
    
    try:
        resp = json.loads(urllib.request.urlopen(req).read())
        count += len(measurements)
        if count % 40 == 0:
            print(f"SEEDER: {count} sent, accepted={resp.get('accepted',0)}, ts={ts}", flush=True)
    except Exception as e:
        print(f"SEEDER_ERROR: {e}", flush=True)
    
    time.sleep(5)
PYEOF

nohup python3 /tmp/live_seeder2.py > /tmp/live_seeder2.log 2>&1 &
echo "SEEDER_PID=$!"

sleep 12
echo "=== SEEDER LOG ==="
cat /tmp/live_seeder2.log

echo "=== TDENGINE CHECK ==="
docker exec plantos-tdengine taos -s "use plantos_ts; select last(*) from d_comp01_motor_current;" 2>&1 | tail -3

echo DONE
