import requests
from datetime import datetime, timezone, timedelta

H = '103.97.132.249'
K = {'X-API-Key': 'plantos-edge-key-2026'}
SID = 'RAW-WATER-QUALITY-STATION-101.raw_turbidity'

# 1. Latest data
r = requests.get(f'http://{H}:8000/api/v1/measurements/history',
    params={'signal_id': SID, 'limit': 1}, headers=K, timeout=10)
d = r.json()
pts = d.get('data', []) if isinstance(d, dict) else []
if pts:
    print(f'Latest: {pts[0]["value"]} @ {pts[0]["timestamp"]}')
    print(f'  Quality: {pts[0].get("quality", "?")}')
else:
    print('NO DATA at all!')

# 2. Last 10 min (UTC)
now = datetime.now(timezone.utc)
ago = now - timedelta(minutes=10)
r2 = requests.get(f'http://{H}:8000/api/v1/measurements/history',
    params={'signal_id': SID, 'from': ago.isoformat(), 'to': now.isoformat(), 'limit': 5},
    headers=K, timeout=10)
d2 = r2.json()
pts2 = d2.get('data', []) if isinstance(d2, dict) else []
print(f'Last 10min UTC ({ago.strftime("%H:%M")} to {now.strftime("%H:%M")}): {len(pts2)} pts')

# 3. Last 12h
ago12 = now - timedelta(hours=12)
r3 = requests.get(f'http://{H}:8000/api/v1/measurements/history',
    params={'signal_id': SID, 'from': ago12.isoformat(), 'to': now.isoformat(), 'limit': 5},
    headers=K, timeout=10)
d3 = r3.json()
pts3 = d3.get('data', []) if isinstance(d3, dict) else []
print(f'Last 12h UTC ({ago12.strftime("%H:%M")} to {now.strftime("%H:%M")}): {len(pts3)} pts')
if pts3:
    for p in pts3[:3]:
        print(f'  {p["value"]} @ {p["timestamp"]}')

# 4. Vietnam time now
vtn = datetime.now(timezone(timedelta(hours=7)))
print(f'\nVietnam time now: {vtn.strftime("%Y-%m-%d %H:%M:%S")}')
print(f'UTC time now: {now.strftime("%Y-%m-%d %H:%M:%S")}')

# 5. Check VF simulator
try:
    r4 = requests.get(f'http://{H}:8100/api/v1/scenarios/current', timeout=5)
    print(f'VF Simulator: {r4.status_code} - {r4.text[:100]}')
except Exception as e:
    print(f'VF Simulator: DOWN - {e}')
