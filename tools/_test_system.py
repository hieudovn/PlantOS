import httpx
r = httpx.post("http://localhost:8000/api/v1/auth/login",
    json={"username":"admin","password":"PlantOS@2026!"}, timeout=10)
token = r.json()["access_token"]
h = {"Authorization": f"Bearer {token}"}

r = httpx.get("http://localhost:8000/api/v1/system/metrics", headers=h, timeout=10)
print(f"HTTP {r.status_code}")
import json
d = r.json()
td = d.get("tdengine", {})
print(f"TDengine: count={td.get('measurement_count')}, size_mb={td.get('size_mb')}")
pg = d.get("postgresql", {})
print(f"PG: size_mb={pg.get('size_mb')}, tables={len(pg.get('tables', {}))}")
