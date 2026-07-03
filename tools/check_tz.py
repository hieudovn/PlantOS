import urllib.request, json
url = "http://localhost:8000/api/v1/measurements/history?signal_id=HSP-101.flow_rate&from=2026-07-03T10%3A00%3A00.000Z&to=2026-07-03T11%3A00%3A00.000Z"
req = urllib.request.Request(url, headers={"X-API-Key": "plantos-edge-8db46bd13a6a1e50b75f854b"})
resp = urllib.request.urlopen(req)
data = json.loads(resp.read())
for pt in data.get("data", [])[:3]:
    print(pt.get("timestamp", "?"))
