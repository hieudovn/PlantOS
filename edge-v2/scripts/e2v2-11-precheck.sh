#!/bin/bash
# E2V2-11 Pre-check
echo "=== E2V2-11 PRE-CHECK ==="
echo "v1: $(curl -s -o /dev/null -w '%{http_code}' http://localhost:8001)"
V2_STATUS=$(python3 -c "import httpx,json;r=httpx.get('http://localhost:8011/api/status',timeout=5);s=json.loads(r.text);print(s.get('status','?'))" 2>/dev/null)
echo "v2: $V2_STATUS"
echo "Center: $(curl -s -o /dev/null -w '%{http_code}' http://localhost:8000/health)"
BL=$(python3 -c "import httpx,json;r=httpx.get('http://localhost:8011/api/status',timeout=5);s=json.loads(r.text);print(s.get('sync',{}).get('backlog','?'))" 2>/dev/null)
echo "backlog: $BL"
echo ""
echo "=== 15 shared signals check ==="
python3 -c "
import httpx,json,os
api='http://localhost:8000/api/v1'
pw=os.environ.get('PLANTOS_CENTER_PASSWORD','PlantOS@2026!')
r=httpx.post(f'{api}/auth/login',json={'username':'admin','password':pw},timeout=10)
t=r.json().get('access_token','')
h={'Authorization':f'Bearer {t}'}
v1=httpx.get(f'{api}/signals?plant_id=DEMO-PLANT',headers=h,timeout=10).json()
v2=httpx.get(f'{api}/signals?plant_id=EDGEV2-DEMO',headers=h,timeout=10).json()
v1s={s['signal_id'] for s in v1 if 'signal_id' in s}
v2s={s['signal_id'] for s in v2 if 'signal_id' in s}
sh=v1s&v2s
print(f'v1 signals: {len(v1s)}')
print(f'v2 signals: {len(v2s)}')
print(f'Shared: {len(sh)}')
for s in sorted(sh):
    print(f'  {s}')
"
