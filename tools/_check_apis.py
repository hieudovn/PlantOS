import httpx

# Login
r = httpx.post("http://localhost:8000/api/v1/auth/login",
    json={"username":"admin","password":"PlantOS@2026!"}, timeout=10)
token = r.json()["access_token"]
h = {"Authorization": f"Bearer {token}"}

# Test signals API
r = httpx.get("http://localhost:8000/api/v1/signals?plant_id=EDGEV2-DEMO", headers=h, timeout=10)
print(f"Signals API: HTTP {r.status_code}")
if r.status_code == 200:
    data = r.json()
    print(f"  Count: {len(data)}")
    for s in data[:5]:
        print(f"  {s.get('signal_id')}: {s.get('display_name')}")
else:
    print(f"  Body: {r.text[:300]}")

# Test plants API
r = httpx.get("http://localhost:8000/api/v1/plants", headers=h, timeout=10)
print(f"\nPlants API: HTTP {r.status_code}")
if r.status_code == 200:
    data = r.json()
    print(f"  Count: {len(data)}")
    for p in data:
        print(f"  {p.get('plant_id')}")

# Test measurements with data
r = httpx.get("http://localhost:8000/api/v1/measurements/history?signal_id=PUMP-101.flow_rate&from=2026-07-09T02:00:00&to=2026-07-09T12:00:00", headers=h, timeout=10)
print(f"\nMeasurements: HTTP {r.status_code}")
if r.status_code == 200:
    d = r.json()
    pts = d.get("data", [])
    print(f"  Points: {len(pts)}")
    if pts:
        print(f"  First: {pts[0]}")
        print(f"  Last: {pts[-1]}")
