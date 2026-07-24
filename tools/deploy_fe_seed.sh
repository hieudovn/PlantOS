#!/bin/bash
set -e
cd /opt/plantos
git fetch origin phase8-closure 2>/dev/null
git checkout -f --detach 91c7671 2>/dev/null || true

echo "=== Build + Deploy Frontend ==="
docker build -f frontend/Dockerfile --target build -t plantos-fe-build frontend 2>&1 | tail -3
CID=$(docker create plantos-fe-build)
docker cp $CID:/app/dist /tmp/new-dist
docker rm $CID
rm -rf /opt/plantos/frontend/dist/*
cp -r /tmp/new-dist/* /opt/plantos/frontend/dist/
nginx -s reload 2>/dev/null || systemctl reload nginx 2>/dev/null

echo "=== Restart Seeder ==="
pkill -f "live_seeder" 2>/dev/null || true
sleep 1

python3 << 'PYEOF' > /tmp/live_seeder.log 2>&1 &
import time, random, json, urllib.request
from datetime import datetime, timezone

CENTER = "http://localhost:8000"
SIGNALS = ["COMP01-MOTOR.current","COMP01-MOTOR.winding_temp",
           "COMP01-MOTOR.motor_power","PUMP-101.flow_rate"]

def login():
    req = urllib.request.Request(f"{CENTER}/api/v1/auth/login",
        data=json.dumps({"username":"admin","password":"PlantOS@2026!"}).encode(),
        headers={"Content-Type":"application/json"})
    return json.loads(urllib.request.urlopen(req).read())["access_token"]

token = login()
count = 0
last_login = time.time()
print(f"SEEDER: STARTED", flush=True)

while True:
    if time.time() - last_login > 1800:
        token = login()
        last_login = time.time()
    
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    measurements = [{"timestamp": ts, "signal_id": s, "value": round(random.uniform(10, 150), 2), "quality": "GOOD"} for s in SIGNALS]
    
    req = urllib.request.Request(f"{CENTER}/api/v1/measurements/ingest",
        data=json.dumps({"source":"live","measurements":measurements}).encode(),
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
    
    try:
        resp = json.loads(urllib.request.urlopen(req).read())
        count += len(measurements)
        if count % 40 == 0:
            print(f"SEEDER: {count} sent, ts={ts}", flush=True)
    except Exception as e:
        print(f"SEEDER_ERR: {e}", flush=True)
        token = login()
        last_login = time.time()
    
    time.sleep(5)
PYEOF

echo "SEEDER_PID=$!"
sleep 8
cat /tmp/live_seeder.log

echo ""
echo "=== Verify ==="
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login -H 'Content-Type: application/json' -d '{"username":"admin","password":"PlantOS@2026!"}' | python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token',''))")
curl -s "http://localhost:8000/api/v1/measurements/history?signal_id=COMP01-MOTOR.current&from=2026-07-23T08:00:00Z&to=2026-07-23T10:00:00Z" \
  -H "Authorization: Bearer $TOKEN" | python3 -c "
import sys,json
d=json.load(sys.stdin)
data=d.get('data',[])
print(f'RECORDS: {len(data)}')
if data: print(f'LATEST: {data[-1].get(\"value\")} @ {data[-1].get(\"timestamp\")}')
"
echo DONE
