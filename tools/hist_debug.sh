#!/bin/bash
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login -H 'Content-Type: application/json' -d '{"username":"admin","password":"PlantOS@2026!"}' | python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token',''))")
echo "TOKEN_OK: ${TOKEN:0:20}..."

echo "=== HISTORIAN RAW ==="
curl -s "http://localhost:8000/api/v1/measurements/history?signal_id=COMP-01.motor_current&from=2026-07-20T00:00&to=2026-07-23T23:59" \
  -H "Authorization: Bearer $TOKEN" | python3 -c "
import sys,json
d=json.load(sys.stdin)
print('KEYS:', list(d.keys())[:5])
for k,v in d.items():
  if isinstance(v,list): print(f'{k}: {len(v)} items')
  elif isinstance(v,dict): print(f'{k}: {len(v)} keys')
  else: print(f'{k}: {str(v)[:100]}')
" 2>&1

echo "=== SIGNALS TEST ==="
curl -s "http://localhost:8000/api/v1/signals?limit=3" \
  -H "Authorization: Bearer $TOKEN" | python3 -c "
import sys,json
d=json.load(sys.stdin)
if isinstance(d,list):
  for s in d[:3]: print(f'  {s.get(\"id\",\"?\")[:20]}')
  print(f'Total: {len(d)} signals')
" 2>&1

echo DONE
