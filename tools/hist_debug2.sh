#!/bin/bash
echo "=== TABLE NAME DEBUG ==="
python3 -c "
sid = 'COMP-01.motor_current'
safe = sid.replace('.','_').replace('-','_').replace(':','_').replace('/','_').replace(' ','_').lower()
print(f'signal_id: {sid}')
print(f'safe_name: {safe}')
print(f'table:     d_{safe}')
print()

# Actual table: d_comp01_motor_current
# Note: comp01 vs comp_01 — the old naming dropped the underscore
print('MISMATCH: d_comp_01_motor_current vs d_comp01_motor_current')
print('FIX: remove underscore between comp and 01')
print()

# Quick fix: just query with wildcard match
"

echo "=== TRY TDENGINE DIRECT ==="
docker exec plantos-tdengine taos -s "use plantos_ts; select last(*) from d_comp01_motor_current;" 2>&1 | tail -5

echo "=== QUICK FIX: UPDATE SIGNAL NAME ==="
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login -H 'Content-Type: application/json' -d '{"username":"admin","password":"PlantOS@2026!"}' | python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token',''))")

# Try with comp01 (no underscore)
curl -s "http://localhost:8000/api/v1/measurements/history?signal_id=comp01.motor_current&from=2026-07-20T00:00&to=2026-07-23T23:59" \
  -H "Authorization: Bearer $TOKEN" | python3 -c "
import sys,json
d=json.load(sys.stdin)
data=d.get('data',[])
print(f'comp01.motor_current -> {len(data)} records')
" 2>&1

# Try with COMP01.motor_current
curl -s "http://localhost:8000/api/v1/measurements/history?signal_id=COMP01.motor_current&from=2026-07-20T00:00&to=2026-07-23T23:59" \
  -H "Authorization: Bearer $TOKEN" | python3 -c "
import sys,json
d=json.load(sys.stdin)
data=d.get('data',[])
print(f'COMP01.motor_current -> {len(data)} records')
" 2>&1

echo DONE
