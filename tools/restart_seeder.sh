#!/bin/bash
# Kill old seeder and start new one
pkill -f "live_seeder" 2>/dev/null || true
sleep 1

nohup python3 -c "
import time, random, json, urllib.request
from datetime import datetime, timezone

CENTER = 'http://localhost:8000'
SIGNALS = ['COMP01-MOTOR.current','COMP01-MOTOR.winding_temp','COMP01-MOTOR.motor_power','PUMP-101.flow_rate']

def login():
    req = urllib.request.Request(f'{CENTER}/api/v1/auth/login',
        data=json.dumps({'username':'admin','password':'PlantOS@2026!'}).encode(),
        headers={'Content-Type':'application/json'})
    return json.loads(urllib.request.urlopen(req).read())['access_token']

token = login()
count = 0
last_login = time.time()
print('SEEDER:STARTED', flush=True)

while True:
    if time.time() - last_login > 1800:
        token = login()
        last_login = time.time()
    ts = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
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

echo "PID=$!"
sleep 10
cat /tmp/live_seeder.log
echo DONE
