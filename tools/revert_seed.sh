#!/bin/bash
# Revert to working edge + start live data seeder

echo "=== Revert Edge ==="
docker stop plantos-edge-v2 2>/dev/null; docker rm plantos-edge-v2 2>/dev/null
docker run -d --name plantos-edge-v2 \
  --network deployment_plantos-net \
  -p 127.0.0.1:8011:8011 \
  -v /tmp/edge_config.yaml:/app/agent/config/config.edge-v2.yaml:ro \
  -e EDGE_CONFIG_PATH=/app/agent/config/config.edge-v2.yaml \
  plantos-edge-v2:patched
sleep 6

echo "=== Edge Log ==="
docker logs plantos-edge-v2 --tail 8 2>&1 | grep -E 'JWT|login|start|heart'

echo "=== Start Live Data Seeder ==="
# Kill any existing seeder
pkill -f "live_seeder" 2>/dev/null || true

cat > /tmp/live_seeder.py << 'PYEOF'
import time, random, requests, os
from datetime import datetime, timezone

CENTER = "http://localhost:8000"
USER = "admin"
PW = "PlantOS@2026!"
SIGNALS = [
    "COMP01-MOTOR.current", "COMP01-MOTOR.winding_temp",
    "COMP01-MOTOR.motor_power", "PUMP-101.flow_rate",
    "FILTER-101.filter_dp", "TANK-101.tank_level"
]

# Login
r = requests.post(f"{CENTER}/api/v1/auth/login", json={"username": USER, "password": PW})
token = r.json()["access_token"]
print(f"SEEDER: LOGIN_OK")

count = 0
while True:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    measurements = []
    for sig in SIGNALS:
        val = round(random.uniform(10, 150), 2)
        measurements.append({"signal_id": sig, "value": val, "timestamp": ts, "quality": 192})
    
    r = requests.post(f"{CENTER}/api/v1/measurements/ingest",
        headers={"Authorization": f"Bearer {token}"},
        json=measurements)
    
    count += len(measurements)
    if count % 60 == 0:
        print(f"SEEDER: {count} measurements sent, last={ts}")
    
    time.sleep(5)
PYEOF

nohup python3 /tmp/live_seeder.py > /tmp/live_seeder.log 2>&1 &
echo "SEEDER_STARTED_PID=$!"

sleep 8
echo "=== Seeder Log ==="
cat /tmp/live_seeder.log

echo "=== TDengine Latest ==="
docker exec plantos-tdengine taos -s "use plantos_ts; select last(*) from d_comp01_motor_current;" 2>&1 | tail -3

echo DONE
