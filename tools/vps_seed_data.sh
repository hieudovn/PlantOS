#!/bin/bash
set -e
cd /opt/plantos

echo "=== Login ==="
RESP=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"PlantOS@2026!"}')

TOKEN=$(echo "$RESP" | python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token',''))" 2>/dev/null)
echo "Token: ${TOKEN:0:20}..."

if [ -z "$TOKEN" ]; then
  echo "Login failed: $RESP"
  exit 1
fi

echo "$TOKEN" > /tmp/plantos_token.txt

echo "=== Seeding DEMO-PLANT ==="
python3 -c "
import httpx, json
api = 'http://localhost:8000/api/v1'
with open('/tmp/plantos_token.txt') as f: token = f.read().strip()
h = {'Authorization': f'Bearer {token}'}
def post(path, data):
    r = httpx.post(f'{api}{path}', json=data, headers=h)
    if r.status_code in (200,201): print(f'  OK {path}')
    else: print(f'  FAIL {path}: {r.status_code} {r.text[:80]}')

post('/plants', {'plant_id':'DEMO-PLANT','name':'Demo Plant','timezone':'Asia/Ho_Chi_Minh'})
post('/areas', {'area_id':'PROCESS-AREA','plant_id':'DEMO-PLANT','name':'Process Area'})
post('/areas', {'area_id':'ELECTRICAL-AREA','plant_id':'DEMO-PLANT','name':'Electrical Area'})
for a in [
    {'asset_id':'LINE-01','name':'Production Line 01','asset_type':'line','area_id':'PROCESS-AREA'},
    {'asset_id':'PUMP-101','name':'Feed Pump 101','asset_type':'pump','area_id':'PROCESS-AREA','parent_asset_id':'LINE-01'},
    {'asset_id':'MOTOR-101','name':'Drive Motor 101','asset_type':'motor','area_id':'PROCESS-AREA','parent_asset_id':'LINE-01'},
    {'asset_id':'TANK-101','name':'Storage Tank 101','asset_type':'tank','area_id':'PROCESS-AREA','parent_asset_id':'LINE-01'},
]:
    post('/assets', a)
for s in [
    ('PUMP-101.flow_rate','PUMP-101','flow_rate','Flow Rate','m3/h','float'),
    ('PUMP-101.discharge_pressure','PUMP-101','discharge_pressure','Discharge Pressure','bar','float'),
    ('MOTOR-101.motor_current','MOTOR-101','motor_current','Motor Current','A','float'),
]:
    body = {'signal_id':s[0],'asset_id':s[1],'signal_name':s[2],'display_name':s[3],'data_type':s[5],'signal_type':'measurement'}
    if s[4]: body['engineering_unit']=s[4]
    body['source']={'source_type':'simulator','source_ref':'sim://'+s[0].replace('.','/')}
    body['uns_path']='avenue/demo-plant/'+s[1]+'/'+s[2]
    post('/signals', body)
print('DEMO-PLANT seeded')
"

echo "=== Seeding EDGEV2-DEMO ==="
python3 -c "
import httpx, json
api = 'http://localhost:8000/api/v1'
with open('/tmp/plantos_token.txt') as f: token = f.read().strip()
h = {'Authorization': f'Bearer {token}'}
def post(path, data):
    r = httpx.post(f'{api}{path}', json=data, headers=h)
    if r.status_code in (200,201): print(f'  OK {path}')
    else: print(f'  FAIL {path}: {r.status_code}')

post('/plants', {'plant_id':'EDGEV2-DEMO','name':'Edge v2 Demo Plant','timezone':'Asia/Ho_Chi_Minh'})
post('/areas', {'area_id':'EDGEV2-DEMO-AREA','plant_id':'EDGEV2-DEMO','name':'Edge v2 Demo Area'})
for a in [
    {'asset_id':'EDGEV2-PUMP-101','name':'Edge v2 Feed Pump 101','asset_type':'pump','area_id':'EDGEV2-DEMO-AREA'},
    {'asset_id':'EDGEV2-TANK-101','name':'Edge v2 Storage Tank 101','asset_type':'tank','area_id':'EDGEV2-DEMO-AREA'},
    {'asset_id':'EDGEV2-MOTOR-101','name':'Edge v2 Drive Motor 101','asset_type':'motor','area_id':'EDGEV2-DEMO-AREA'},
    {'asset_id':'EDGEV2-QUALITY-STATION-101','name':'Edge v2 Quality Station 101','asset_type':'quality_station','area_id':'EDGEV2-DEMO-AREA'},
    {'asset_id':'EDGEV2-ENERGY-METER-101','name':'Edge v2 Energy Meter 101','asset_type':'energy_meter','area_id':'EDGEV2-DEMO-AREA'},
]:
    post('/assets', a)
for s in [
    ('EDGEV2-PUMP-101.flow_rate','EDGEV2-PUMP-101','flow_rate','Flow Rate','m3/h','float'),
    ('EDGEV2-PUMP-101.discharge_pressure','EDGEV2-PUMP-101','discharge_pressure','Discharge Pressure','bar','float'),
    ('EDGEV2-PUMP-101.vibration','EDGEV2-PUMP-101','vibration','Vibration','mm/s','float'),
    ('EDGEV2-TANK-101.level','EDGEV2-TANK-101','level','Tank Level','%','float'),
    ('EDGEV2-MOTOR-101.running_status','EDGEV2-MOTOR-101','running_status','Running Status','','bool'),
    ('EDGEV2-QUALITY-STATION-101.turbidity','EDGEV2-QUALITY-STATION-101','turbidity','Turbidity','NTU','float'),
    ('EDGEV2-ENERGY-METER-101.active_power','EDGEV2-ENERGY-METER-101','active_power','Active Power','kW','float'),
]:
    body = {'signal_id':s[0],'asset_id':s[1],'signal_name':s[2],'display_name':s[3],'data_type':s[5],'signal_type':'measurement'}
    if s[4]: body['engineering_unit']=s[4]
    body['source']={'source_type':'simulator','source_ref':'sim://'+s[0].replace('.','/')}
    body['uns_path']='avenue/edgev2-demo/'+s[1]+'/'+s[2]
    post('/signals', body)
print('EDGEV2-DEMO seeded')
"

echo "=== Verify ==="
curl -s -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/plants | \
  python3 -c "import sys,json; [print('  '+p['plant_id']) for p in json.load(sys.stdin)]"

echo "=== Running comparison ==="
python3 tools/compare_v1_v2_data.py --center-url http://localhost:8000 --hours 1 2>&1 || true

echo "=== DONE ==="
