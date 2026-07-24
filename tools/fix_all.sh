#!/bin/bash
# Restart seeder with auto token refresh + build deploy frontend

cd /opt/plantos
git fetch origin phase8-closure 2>/dev/null
git checkout -f --detach 9b914b5 2>/dev/null || true

# Fix TrendChart.tsx in working tree
python3 -c "
import re
p='frontend/src/features/historian/TrendChart.tsx'
c=open(p).read()
# Replace toLocalFormat
old='''  const toLocalFormat = (ts: string): string => {
    // If already in local format (YYYY-MM-DDTHH:mm), convert to UTC for API
    if (/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$/.test(ts)) {
      // Append +07:00 to indicate Vietnam timezone
      return ts + ':00+07:00';
    }
    // If UTC ISO, convert to local date string
    try {
      const d = new Date(ts);
      if (!isNaN(d.getTime())) {
        return d.toISOString();
      }
    } catch {}
    return ts;
  };'''
new='''  const toLocalFormat = (ts: string): string => {
    const d = new Date(ts);
    if (!isNaN(d.getTime())) return d.toISOString();
    return ts;
  };'''
c=c.replace(old,new)
open(p,'w').write(c)
print('TZ_FIX_APPLIED')
"

echo "=== Build Frontend ==="
docker build -f frontend/Dockerfile --target build -t plantos-fe-build frontend 2>&1 | tail -3
CID=$(docker create plantos-fe-build)
docker cp $CID:/app/dist /tmp/new-dist3
docker rm $CID
rm -rf /opt/plantos/frontend/dist/*
cp -r /tmp/new-dist3/* /opt/plantos/frontend/dist/
nginx -s reload 2>/dev/null || systemctl reload nginx 2>/dev/null
echo "FRONTEND_DEPLOYED"

echo "=== Restart Seeder ==="
pkill -f "live_seeder" 2>/dev/null || true
cat > /tmp/live_seeder3.py << 'PYEOF'
import time, random, json, urllib.request, os
from datetime import datetime, timezone

CENTER = "http://localhost:8000"
USER = "admin"
PW = "PlantOS@2026!"
SIGNALS = ["COMP01-MOTOR.current","COMP01-MOTOR.winding_temp",
           "COMP01-MOTOR.motor_power","PUMP-101.flow_rate"]

def login():
    req = urllib.request.Request(f"{CENTER}/api/v1/auth/login",
        data=json.dumps({"username":USER,"password":PW}).encode(),
        headers={"Content-Type":"application/json"})
    return json.loads(urllib.request.urlopen(req).read())["access_token"]

token = login()
count = 0
last_login = time.time()
print(f"SEEDER: STARTED", flush=True)

while True:
    if time.time() - last_login > 1800:  # Refresh token every 30 min
        token = login()
        last_login = time.time()
    
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    measurements = []
    for sig in SIGNALS:
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
            print(f"SEEDER: {count} total, accepted={resp.get('accepted',0)}, ts={ts}", flush=True)
    except Exception as e:
        print(f"SEEDER_ERROR: {e}", flush=True)
        token = login()  # Re-login on error
        last_login = time.time()
    
    time.sleep(5)
PYEOF

nohup python3 /tmp/live_seeder3.py > /tmp/live_seeder3.log 2>&1 &
echo "SEEDER_RESTARTED_PID=$!"

sleep 10
cat /tmp/live_seeder3.log

echo "=== Verify ==="
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login -H 'Content-Type: application/json' -d '{"username":"admin","password":"PlantOS@2026!"}' | python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token',''))")
curl -s "http://localhost:8000/api/v1/measurements/history?signal_id=COMP01-MOTOR.current&from=2026-07-23T08:00:00Z&to=2026-07-23T10:00:00Z" \
  -H "Authorization: Bearer $TOKEN" | python3 -c "
import sys,json
d=json.load(sys.stdin)
print(f'DATA: {len(d.get(\"data\",[]))} records')
if d.get('data'): print(f'LATEST: {d[\"data\"][-1]}')
" 2>&1

echo DONE
