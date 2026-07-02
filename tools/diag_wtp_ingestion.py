"""WTP Ingestion Diagnostic — kiểm tra toàn bộ pipeline từ Edge → Center → TDengine"""
import requests, json, sys

HOST = "103.97.132.249"
API_KEY = "plantos-edge-key-2026"
HEADERS = {"X-API-Key": API_KEY}

def check(label, url, expect_status=200):
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        ok = r.status_code == expect_status
        print(f"  {'✅' if ok else '❌'} {label}: HTTP {r.status_code}")
        return r if ok else None
    except Exception as e:
        print(f"  ❌ {label}: {e}")
        return None

print("=" * 60)
print("WTP INGESTION DIAGNOSTIC")
print("=" * 60)

# 1. PlantOS health
print("\n--- 1. PlantOS Health ---")
r = check("Health", f"http://{HOST}:8000/health")
if r:
    print(f"    Version: {r.json().get('version', '?')}")

# 2. Check WTP signals exist
print("\n--- 2. WTP Signal Registry ---")
r = check("List WTP signals", f"http://{HOST}:8000/api/v1/signals?plant_id=WTP-DEMO-01")
if r:
    signals = r.json().get("signals", r.json() if isinstance(r.json(), list) else [])
    print(f"    Total WTP signals: {len(signals)}")

# 3. Check current values for key WTP signals
print("\n--- 3. Current Values (5 key WTP signals) ---")
key_signals = [
    "RAW-WATER-QUALITY-STATION-101.raw_turbidity",
    "CLARIFIER-101.settled_turbidity",
    "FILTER-QUALITY-STATION-101.filtered_turbidity",
    "TRANSFER-OUTLET-QUALITY-STATION-101.outlet_turbidity",
    "PLANT-KPI-101.cost_per_m3",
]
for sid in key_signals:
    try:
        r = requests.get(
            f"http://{HOST}:8000/api/v1/measurements/history",
            params={"signal_id": sid, "from": "2026-07-02T00:00:00Z", "to": "2026-07-02T23:59:59Z", "limit": "1"},
            headers=HEADERS, timeout=10
        )
        if r.status_code == 200:
            data = r.json()
            # Handle different response formats
            if isinstance(data, list) and len(data) > 0:
                pts = data if isinstance(data[0], dict) else []
                print(f"  ✅ {sid}: {len(pts)} points")
            elif isinstance(data, dict):
                pts = data.get("measurements", data.get("data", []))
                print(f"  ✅ {sid}: {len(pts)} points in response")
            else:
                print(f"  ⚠️  {sid}: empty response")
        else:
            print(f"  ❌ {sid}: HTTP {r.status_code}")
    except Exception as e:
        print(f"  ❌ {sid}: {e}")

# 4. Try measurement ingest directly to verify pipeline
print("\n--- 4. Test Measurement Ingest ---")
test_payload = {
    "measurements": [{
        "timestamp": "2026-07-02T12:00:00.000Z",
        "signal_id": "RAW-WATER-QUALITY-STATION-101.raw_turbidity",
        "value": 99.9,
        "quality": "GOOD",
        "source": "diag-script"
    }]
}
try:
    r = requests.post(
        f"http://{HOST}:8000/api/v1/measurements/ingest",
        json=test_payload, headers=HEADERS, timeout=10
    )
    if r.status_code == 200:
        print(f"  ✅ Ingest test: HTTP 200")
        print(f"    Response: {json.dumps(r.json(), indent=2)[:200]}")
    else:
        print(f"  ❌ Ingest test: HTTP {r.status_code}")
        print(f"    {r.text[:300]}")
except Exception as e:
    print(f"  ❌ Ingest test: {e}")

# 5. Check Edge Agent status
print("\n--- 5. Edge Agent Status ---")
try:
    r = requests.get(f"http://{HOST}:8000/api/v1/edge/nodes", headers=HEADERS, timeout=10)
    if r.status_code == 200:
        nodes = r.json() if isinstance(r.json(), list) else r.json().get("nodes", [])
        print(f"  Edge nodes: {len(nodes)}")
        for n in nodes[:5]:
            print(f"    {n.get('node_id', '?')} | status={n.get('status', '?')} | last_heartbeat={n.get('last_heartbeat', '?')}")
    else:
        print(f"  ❌ HTTP {r.status_code}")
except Exception as e:
    print(f"  ⚠️  Edge nodes endpoint: {e} (may not exist yet)")

# 6. Check VF Simulator status
print("\n--- 6. VF WTP Simulator Status ---")
for endpoint, label in [
    ("/api/v1/scenarios/current", "Scenario"),
    ("/health", "Health"),
]:
    try:
        r = requests.get(f"http://{HOST}:8100{endpoint}", timeout=5)
        print(f"  {'✅' if r.status_code == 200 else '❌'} VF {label}: HTTP {r.status_code}")
        if r.status_code == 200:
            print(f"    {r.text[:200]}")
    except Exception as e:
        print(f"  ❌ VF {label}: {e}")

# 7. Summary
print("\n" + "=" * 60)
print("DIAGNOSTIC COMPLETE")
print("=" * 60)
print("\nCheck the results above. Key things to look for:")
print("  - Section 3: If current values return empty → data not in TDengine")
print("  - Section 4: If ingest test SUCCEEDS → pipeline works, data source issue")
print("  - Section 4: If ingest test FAILS → pipeline broken, check backend logs")
print("  - Section 5: Edge Agent not showing WTP → need to configure OPC UA collector")
print("  - Section 6: VF simulator down → restart it on port 8100")
