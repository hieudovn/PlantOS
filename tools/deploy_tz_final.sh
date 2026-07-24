#!/bin/bash
set -e
# 1. Restart seeder with VN time
pkill -f "live_seeder" 2>/dev/null || true
sleep 1

nohup python3 -c "
import time, random, json, urllib.request
from datetime import datetime, timezone, timedelta
CENTER='http://localhost:8000'
VN=timezone(timedelta(hours=7))
S='COMP01-MOTOR.current','COMP01-MOTOR.winding_temp','COMP01-MOTOR.motor_power','PUMP-101.flow_rate'
def L():
    r=urllib.request.Request(f'{CENTER}/api/v1/auth/login',data=json.dumps({'username':'admin','password':'PlantOS@2026!'}).encode(),headers={'Content-Type':'application/json'})
    return json.loads(urllib.request.urlopen(r).read())['access_token']
t=L()
c=0;ll=time.time()
print('SEEDER:VN_TIME',flush=True)
while True:
    if time.time()-ll>1800:t=L();ll=time.time()
    ts=datetime.now(VN).strftime('%Y-%m-%dT%H:%M:%S+07:00')
    m=[{'timestamp':ts,'signal_id':s,'value':round(random.uniform(10,150),2),'quality':'GOOD'}for s in S]
    r=urllib.request.Request(f'{CENTER}/api/v1/measurements/ingest',data=json.dumps({'source':'live','measurements':m}).encode(),headers={'Authorization':f'Bearer {t}','Content-Type':'application/json'})
    try:
        j=json.loads(urllib.request.urlopen(r).read());c+=4
        if c%40==0:print(f'S:{c}@{ts}',flush=True)
    except:t=L();ll=time.time()
    time.sleep(5)
" > /tmp/seeder.log 2>&1 &
echo "SEEDER=$!"

# 2. Build + deploy frontend
cd /opt/plantos
git fetch origin phase8-closure 2>/dev/null
git checkout -f --detach cfd64f3 2>/dev/null || true
docker build -f frontend/Dockerfile --target build -t plantos-fe-build frontend 2>&1 | tail -3
CID=$(docker create plantos-fe-build)
docker cp $CID:/app/dist /tmp/new-dist
docker rm $CID
rm -rf /opt/plantos/frontend/dist/*
cp -r /tmp/new-dist/* /opt/plantos/frontend/dist/
nginx -s reload 2>/dev/null || systemctl reload nginx 2>/dev/null

# 3. Verify
sleep 10
echo "=== Seeder ==="
head -5 /tmp/seeder.log
echo "=== Data ==="
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login -H 'Content-Type: application/json' -d '{"username":"admin","password":"PlantOS@2026!"}' | python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token',''))")
curl -s "http://localhost:8000/api/v1/measurements/history?signal_id=COMP01-MOTOR.current&from=2026-07-23T16:00:00%2B07:00&to=2026-07-23T18:00:00%2B07:00" -H "Authorization: Bearer $TOKEN" | python3 -c "
import sys,json;d=json.load(sys.stdin);data=d.get('data',[]);print(f'RECORDS:{len(data)}')
if data:print(f'LATEST:{data[-1].get(\"timestamp\")} = {data[-1].get(\"value\")}')
"
echo DONE
