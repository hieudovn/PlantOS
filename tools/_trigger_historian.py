import httpx
r = httpx.post("http://localhost:8000/api/v1/auth/login",
    json={"username":"admin","password":"PlantOS@2026!"}, timeout=10)
token = r.json()["access_token"]
h = {"Authorization": f"Bearer {token}"}

# Trigger historian by querying measurements
r = httpx.get("http://localhost:8000/api/v1/measurements/history?signal_id=PUMP-101.flow_rate&from=2026-07-09T00:00:00&to=2026-07-09T12:00:00",
    headers=h, timeout=10)
print(f"History: HTTP {r.status_code}, body: {r.text[:200]}")
