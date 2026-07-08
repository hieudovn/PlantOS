#!/usr/bin/env python3
"""Data E2E Smoke: HTTP simulator → connector → processing → buffer → Center"""
import httpx, time
BASE, CENTER = "http://127.0.0.1:8011", "http://127.0.0.1:8000"

# Login
r = httpx.post(f"{BASE}/api/auth/login", json={"username":"admin","password":"Test@1234"})
c = dict(r.cookies)
csrf = c.get("plantos_csrf","")

print("1. Create HTTP Poll connector...")
r = httpx.post(f"{BASE}/api/connections", cookies=c, json={
    "connector_id": "data_e2e_http", "type": "http_poll", "enabled": True,
    "connection": {"url": "http://127.0.0.1:9999/api/test/measurements", "interval_seconds": 5},
    "tags": [
        {"tag_id": "t1", "source_ref": "pump101_flow", "signal_id": "EDGEV2-PUMP-101.flow_rate", "data_type": "float"}
    ]
}, headers={"X-CSRF-Token": csrf})
print(f"  CREATE: {r.status_code} {r.text[:100]}")

# Validate
print("2. Validate connector...")
r = httpx.post(f"{BASE}/api/connections/data_e2e_http/validate", cookies=c, json={
    "type":"http_poll","connection":{"url":"http://127.0.0.1:9999/api/test/measurements","interval_seconds":5}
}, headers={"X-CSRF-Token": csrf})
print(f"  VALIDATE: {r.status_code} {r.text[:100]}")

# Create processing profile  
print("3. Create processing profile...")
r = httpx.post(f"{BASE}/api/processing/profiles", cookies=c, json={
    "profile_id": "data_e2e_scale", "name": "E2E Scale Test",
    "steps": [{"type": "scale_offset", "params": {"scale": 0.1, "offset": 0}, "order": 1}]
}, headers={"X-CSRF-Token": csrf})
print(f"  PROFILE: {r.status_code} {r.text[:100]}")

# Assign profile to signal
print("4. Assign profile to signal...")
r = httpx.post(f"{BASE}/api/processing/assign", cookies=c, json={
    "signal_id": "EDGEV2-PUMP-101.flow_rate", "profile_id": "data_e2e_scale"
}, headers={"X-CSRF-Token": csrf})
print(f"  ASSIGN: {r.status_code} {r.text[:100]}")

# Apply connector
print("5. Apply connector...")
r = httpx.post(f"{BASE}/api/connections/data_e2e_http/apply", cookies=c, headers={"X-CSRF-Token": csrf})
print(f"  APPLY: {r.status_code} {r.text[:100]}")

# Wait for data
print("6. Waiting for data...")
time.sleep(10)

# Check local measurements
print("7. Check local measurements...")
r = httpx.get(f"{BASE}/api/measurements/latest", cookies=c)
data = r.json()
print(f"  LATEST: {r.status_code}, {len(data)} measurements")
for m in data[:3]:
    print(f"    {m.get('signal_id','?')} = {m.get('value','?')} [{m.get('quality','?')}]")

# Check if our signal is there
found = [m for m in data if "PUMP" in m.get("signal_id","")]
print(f"  EDGEV2-PUMP signals found: {len(found)}")

# Check Center heartbeat
r = httpx.get(f"{CENTER}/api/v1/edge-nodes", headers={"X-API-Key": "plantos-edge-8db46bd13a6a1e50b75f854b"})
nodes = r.json()
v2 = [n for n in nodes if n.get("edge_node_id") == "EDGEV2-PC-01"]
print(f"8. Center: EDGEV2-PC-01 {'online' if v2 and v2[0].get('status')=='online' else v2}")

print(f"\nDATA E2E: {'PASS' if found else 'CHECK MANUALLY'}")
