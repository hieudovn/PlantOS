#!/bin/bash
# Fix: Use VN time (+07:00) consistently for ALL timestamps
# This ensures browser VN time matches stored VN time

# 1. Kill old seeder
pkill -f "live_seeder" 2>/dev/null || true
sleep 1

# 2. Restart seeder with VN time timestamps
nohup python3 -c "
import time, random, json, urllib.request
from datetime import datetime, timezone, timedelta

CENTER = 'http://localhost:8000'
VN = timezone(timedelta(hours=7))
SIGNALS = ['COMP01-MOTOR.current','COMP01-MOTOR.winding_temp','COMP01-MOTOR.motor_power','PUMP-101.flow_rate']

def login():
    req = urllib.request.Request(f'{CENTER}/api/v1/auth/login',
        data=json.dumps({'username':'admin','password':'PlantOS@2026!'}).encode(),
        headers={'Content-Type':'application/json'})
    return json.loads(urllib.request.urlopen(req).read())['access_token']

token = login()
count = 0
last_login = time.time()
print('SEEDER:STARTED (VN timezone)', flush=True)

while True:
    if time.time() - last_login > 1800:
        token = login()
        last_login = time.time()
    
    # Use VN time with +07:00 offset
    now_vn = datetime.now(VN)
    ts = now_vn.strftime('%Y-%m-%dT%H:%M:%S+07:00')
    measurements = [{'timestamp': ts, 'signal_id': s, 'value': round(random.uniform(10,150),2), 'quality':'GOOD'} for s in SIGNALS]
    req = urllib.request.Request(f'{CENTER}/api/v1/measurements/ingest',
        data=json.dumps({'source':'live','measurements':measurements}).encode(),
        headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'})
    try:
        resp = json.loads(urllib.request.urlopen(req).read())
        count += len(measurements)
        if count % 40 == 0: print(f'SEEDER:{count} ts={ts}', flush=True)
    except Exception as e:
        print(f'ERR:{e}', flush=True)
        token = login()
        last_login = time.time()
    time.sleep(5)
" > /tmp/live_seeder.log 2>&1 &

echo "SEEDER_PID=$!"
sleep 8
cat /tmp/live_seeder.log

# 3. Verify data with VN time query
echo ""
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login -H 'Content-Type: application/json' -d '{"username":"admin","password":"PlantOS@2026!"}' | python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token',''))")
NOW_VN=$(date -d '7 hours ago' +%Y-%m-%dT%H:%M 2>/dev/null || python3 -c "from datetime import datetime,timezone,timedelta; print((datetime.now(timezone(timedelta(hours=7)))-timedelta(hours=1)).strftime('%Y-%m-%dT%H:00'))")

echo "Query from: $(python3 -c "from datetime import datetime,timezone,timedelta; print((datetime.now(timezone(timedelta(hours=7)))-timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M'))")"

curl -s "http://localhost:8000/api/v1/measurements/history?signal_id=COMP01-MOTOR.current&from=2026-07-23T15:00:00+07:00&to=2026-07-23T18:00:00+07:00" \
  -H "Authorization: Bearer $TOKEN" | python3 -c "
import sys,json
d=json.load(sys.stdin)
data=d.get('data',[])
print(f'RECORDS: {len(data)}')
if data: print(f'LATEST: {data[-1]}')
"

echo DONE
