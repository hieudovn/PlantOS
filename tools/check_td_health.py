import urllib.request, json

API = "http://localhost:8000"

# 1. Login to get token
data = json.dumps({"username": "admin", "password": "PlantOS@2026!"}).encode()
req = urllib.request.Request(f"{API}/api/v1/auth/login", data=data, headers={"Content-Type": "application/json"})
resp = urllib.request.urlopen(req)
token = json.loads(resp.read())["access_token"]
print(f"Login OK, token: {token[:20]}...")

# 2. System metrics with JWT
req2 = urllib.request.Request(f"{API}/api/v1/system/metrics", headers={"Authorization": f"Bearer {token}"})
resp2 = urllib.request.urlopen(req2)
metrics = json.loads(resp2.read())
td = metrics.get("tdengine", {})
print(f"TDengine: count={td.get('measurement_count')} size_mb={td.get('size_mb')}")

# 3. Check tdengine-data mount
import subprocess
try:
    result = subprocess.run(["du", "-sb", "/tdengine-data"], capture_output=True, text=True, timeout=10)
    print(f"Mount OK: {result.stdout.strip() if result.returncode == 0 else 'FAIL: ' + result.stderr}")
except Exception as e:
    print(f"Mount FAIL: {e}")
