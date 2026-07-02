"""Check available PlantOS API endpoints and try historian query."""
import json

import requests

HOST = "http://localhost:8000"
HEADERS = {"X-API-Key": "plantos-edge-key-2026"}

# List available API paths
print("=== Available Signal/Measurement/Historian Endpoints ===")
r = requests.get(f"{HOST}/openapi.json", headers=HEADERS)
spec = r.json()
for path in sorted(spec.get("paths", {}).keys()):
    if any(k in path.lower() for k in ["signal", "measurement", "historian", "current", "latest"]):
        methods = list(spec["paths"][path].keys())
        print(f"  {path} [{','.join(methods)}]")
print()

# Try signals list
print("=== GET /api/v1/signals (first 3) ===")
r = requests.get(f"{HOST}/api/v1/signals?plant_id=WTP-DEMO-01", headers=HEADERS)
if r.status_code == 200:
    signals = r.json()
    print(f"Total: {len(signals)}")
    for s in signals[:3]:
        print(f"  Signal: {s.get('signal_id')}")
else:
    print(f"HTTP {r.status_code}: {r.text[:200]}")

# Try individual signal
if signals:
    sid = signals[0]["signal_id"]
    print(f"\n=== GET /api/v1/signals/{sid} ===")
    r = requests.get(f"{HOST}/api/v1/signals/{sid}", headers=HEADERS)
    print(f"HTTP {r.status_code}: {r.text[:200]}")

# Try measurements latest
print(f"\n=== POST /api/v1/measurements/latest ===")
r = requests.post(
    f"{HOST}/api/v1/measurements/latest",
    headers={**HEADERS, "Content-Type": "application/json"},
    json={"signal_ids": [signals[0]["signal_id"]]} if signals else ["test"],
)
print(f"HTTP {r.status_code}: {r.text[:500]}")
