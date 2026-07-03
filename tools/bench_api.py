import urllib.request, json, time

ENDPOINTS = [
    ("GET /health", "http://localhost:8000/health", None),
    ("POST /auth/login", "http://localhost:8000/api/v1/auth/login", {"username": "admin", "password": "PlantOS@2026!"}),
    ("GET /users", "http://localhost:8000/api/v1/users", None),
    ("GET /plants", "http://localhost:8000/api/v1/plants", None),
    ("GET /signals", "http://localhost:8000/api/v1/signals", None),
    ("GET /assets", "http://localhost:8000/api/v1/assets", None),
    ("GET /alarms", "http://localhost:8000/api/v1/alarms?state=active", None),
    ("GET /edge-nodes", "http://localhost:8000/api/v1/edge-nodes", None),
    ("GET /system/metrics", "http://localhost:8000/api/v1/system/metrics", None),
    ("GET /history (1 signal, 1h)", "http://localhost:8000/api/v1/measurements/history?signal_id=HSP-101.flow_rate&from=2026-07-03T12:00:00.000Z&to=2026-07-03T13:00:00.000Z", None),
    ("GET /history (1 signal, 24h)", "http://localhost:8000/api/v1/measurements/history?signal_id=HSP-101.flow_rate&from=2026-07-02T13:00:00.000Z&to=2026-07-03T13:00:00.000Z", None),
]

API_KEY = "plantos-edge-8db46bd13a6a1e50b75f854b"

# First get a token
data = json.dumps(ENDPOINTS[1][2]).encode()
req = urllib.request.Request(ENDPOINTS[1][1], data=data, headers={"Content-Type": "application/json"})
resp = urllib.request.urlopen(req)
token = json.loads(resp.read())["access_token"]

for name, url, body in ENDPOINTS:
    headers = {"Authorization": f"Bearer {token}", "X-API-Key": API_KEY}
    if body:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body).encode()
        req = urllib.request.Request(url, data=data, headers=headers)
    else:
        req = urllib.request.Request(url, headers=headers)
    
    start = time.time()
    try:
        resp = urllib.request.urlopen(req, timeout=15)
        result = resp.read()
        elapsed = (time.time() - start) * 1000
        size_kb = len(result) / 1024
        # Quick parse for row count
        try:
            d = json.loads(result)
            if isinstance(d, list):
                count = len(d)
            elif isinstance(d, dict) and "data" in d:
                count = len(d["data"])
            elif isinstance(d, dict) and "tdengine" in d:
                count = f"sys: CPU {d.get('system',{}).get('cpu_percent','?')}%"
            else:
                count = "ok"
        except:
            count = "?"
        print(f"{elapsed:8.0f}ms | {size_kb:7.1f}KB | {count:>20} | {name}")
    except Exception as e:
        elapsed = (time.time() - start) * 1000
        print(f"{elapsed:8.0f}ms | {'ERR':>7} | {str(e)[:40]:>20} | {name}")
