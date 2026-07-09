#!/bin/bash
set -e
cd /home/plantos

echo "=== Getting token ==="
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"PlantOS@2026"}' | \
  python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token',''))")

if [ -z "$TOKEN" ]; then
  echo "Failed to get token - trying X-API-Key"
  AUTH_HEADER="X-API-Key: plantos-edge-key-2026"
else
  AUTH_HEADER="Authorization: Bearer $TOKEN"
fi

echo "=== Checking plants ==="
for plant in DEMO-PLANT EDGEV2-DEMO EDGEV2-TEST; do
  RESP=$(curl -s -o /dev/null -w "%{http_code}" -H "$AUTH_HEADER" "http://localhost:8000/api/v1/plants/$plant" 2>/dev/null)
  echo "$plant: $RESP"
done

echo "=== Seeding via API (using X-API-Key) ==="
python3 -c "
import httpx
api = 'http://localhost:8000/api/v1'
headers = {'X-API-Key': 'plantos-edge-key-2026'}

def post(path, data):
    resp = httpx.post(f'{api}{path}', json=data, headers=headers)
    if resp.status_code in (200, 201):
        print(f'  OK {path}')
    else:
        print(f'  FAIL {path}: {resp.status_code} {resp.text[:100]}')

# Check if plants already exist
resp = httpx.get(f'{api}/plants', headers=headers)
existing = [p['plant_id'] for p in resp.json()] if resp.status_code == 200 else []
print(f'Existing plants: {existing}')

if 'DEMO-PLANT' not in existing:
    print('Seeding DEMO-PLANT...')
    for item in [{'plant_id': 'DEMO-PLANT', 'name': 'Demo Plant', 'timezone': 'Asia/Ho_Chi_Minh'}]:
        post('/plants', item)
    for area in [
        {'area_id': 'PROCESS-AREA', 'plant_id': 'DEMO-PLANT', 'name': 'Process Area'},
        {'area_id': 'ELECTRICAL-AREA', 'plant_id': 'DEMO-PLANT', 'name': 'Electrical Area'}
    ]:
        post('/areas', area)
    for asset in [
        {'asset_id': 'LINE-01', 'name': 'Production Line 01', 'asset_type': 'line', 'area_id': 'PROCESS-AREA'},
        {'asset_id': 'PUMP-101', 'name': 'Feed Pump 101', 'asset_type': 'pump', 'area_id': 'PROCESS-AREA', 'parent_asset_id': 'LINE-01'},
        {'asset_id': 'MOTOR-101', 'name': 'Drive Motor 101', 'asset_type': 'motor', 'area_id': 'PROCESS-AREA', 'parent_asset_id': 'LINE-01'},
        {'asset_id': 'TANK-101', 'name': 'Storage Tank 101', 'asset_type': 'tank', 'area_id': 'PROCESS-AREA', 'parent_asset_id': 'LINE-01'},
    ]:
        post('/assets', asset)
    for sig in [
        ('PUMP-101.flow_rate', 'PUMP-101', 'flow_rate', 'Flow Rate', 'm3/h', 'float'),
        ('PUMP-101.discharge_pressure', 'PUMP-101', 'discharge_pressure', 'Discharge Pressure', 'bar', 'float'),
        ('MOTOR-101.motor_current', 'MOTOR-101', 'motor_current', 'Motor Current', 'A', 'float'),
    ]:
        body = {'signal_id': sig[0], 'asset_id': sig[1], 'signal_name': sig[2], 'display_name': sig[3], 'data_type': sig[5], 'signal_type': 'measurement'}
        if sig[4]: body['engineering_unit'] = sig[4]
        body['source'] = {'source_type': 'simulator', 'source_ref': 'sim://' + sig[0].replace('.','/')}
        body['uns_path'] = 'avenue/demo-plant/' + sig[1] + '/' + sig[2]
        post('/signals', body)
    print('DEMO-PLANT seeded')
else:
    print('DEMO-PLANT already exists')

if 'EDGEV2-DEMO' not in existing:
    print('Seeding EDGEV2-DEMO...')
    exec(open('scripts/seed_edgev2_demo.py').read().replace('if __name__', 'if False'))
    # Use inline approach
    post('/plants', {'plant_id': 'EDGEV2-DEMO', 'name': 'Edge v2 Demo Plant', 'timezone': 'Asia/Ho_Chi_Minh'})
    post('/areas', {'area_id': 'EDGEV2-DEMO-AREA', 'plant_id': 'EDGEV2-DEMO', 'name': 'Edge v2 Demo Area'})
    for a in [
        {'asset_id': 'EDGEV2-PUMP-101', 'name': 'Edge v2 Feed Pump 101', 'asset_type': 'pump', 'area_id': 'EDGEV2-DEMO-AREA'},
        {'asset_id': 'EDGEV2-TANK-101', 'name': 'Edge v2 Storage Tank 101', 'asset_type': 'tank', 'area_id': 'EDGEV2-DEMO-AREA'},
        {'asset_id': 'EDGEV2-MOTOR-101', 'name': 'Edge v2 Drive Motor 101', 'asset_type': 'motor', 'area_id': 'EDGEV2-DEMO-AREA'},
    ]:
        post('/assets', a)
    for sig in [
        ('EDGEV2-PUMP-101.flow_rate', 'EDGEV2-PUMP-101', 'flow_rate', 'Flow Rate', 'm3/h', 'float'),
        ('EDGEV2-PUMP-101.discharge_pressure', 'EDGEV2-PUMP-101', 'discharge_pressure', 'Discharge Pressure', 'bar', 'float'),
        ('EDGEV2-MOTOR-101.running_status', 'EDGEV2-MOTOR-101', 'running_status', 'Running Status', '', 'bool'),
    ]:
        body = {'signal_id': sig[0], 'asset_id': sig[1], 'signal_name': sig[2], 'display_name': sig[3], 'data_type': sig[5], 'signal_type': 'measurement'}
        if sig[4]: body['engineering_unit'] = sig[4]
        body['source'] = {'source_type': 'simulator', 'source_ref': 'sim://' + sig[0].replace('.','/')}
        body['uns_path'] = 'avenue/edgev2-demo/' + sig[1] + '/' + sig[2]
        post('/signals', body)
    print('EDGEV2-DEMO seeded')
else:
    print('EDGEV2-DEMO already exists')

print('Seeding complete')
"
