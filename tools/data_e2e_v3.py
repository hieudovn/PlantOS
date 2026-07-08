#!/usr/bin/env python3
"""Data E2E v3 — delete old connector, redeploy fix, re-create, start, verify"""
import httpx, time
BASE = "http://127.0.0.1:8011"

r = httpx.post(f"{BASE}/api/auth/login", json={"username":"admin","password":"Test@1234"})
c = dict(r.cookies)
csrf = c.get("plantos_csrf","")

# 1. Delete old connector if exists
print("1. Clean up old connector...")
r = httpx.delete(f"{BASE}/api/connections/data_e2e_http", cookies=c, headers={"X-CSRF-Token": csrf})
print(f"   DELETE: {r.status_code}")

# 2. Create new connector
print("2. Create HTTP Poll connector...")
r = httpx.post(f"{BASE}/api/connections", cookies=c, json={
    "connector_id": "data_e2e_http", "type": "http_poll", "enabled": True,
    "connection": {"url": "http://127.0.0.1:9999/api/test/measurements", "interval_seconds": 5, "method": "GET"},
    "tags": [{"tag_id": "t1", "source_ref": "pump101_flow", "signal_id": "EDGEV2-PUMP-101.flow_rate", "data_type": "float"}]
}, headers={"X-CSRF-Token": csrf})
print(f"   CREATE: {r.status_code} {r.text[:100]}")

# 3. Apply (should register in runtime)
print("3. Apply connector...")
r = httpx.post(f"{BASE}/api/connections/data_e2e_http/apply", cookies=c, headers={"X-CSRF-Token": csrf})
print(f"   APPLY: {r.status_code} {r.text[:120]}")

# 4. Start
print("4. Start connector...")
r = httpx.post(f"{BASE}/api/connections/data_e2e_http/start", cookies=c, headers={"X-CSRF-Token": csrf})
print(f"   START: {r.status_code} {r.text[:80]}")

# 5. Check status
r = httpx.get(f"{BASE}/api/connections/data_e2e_http", cookies=c)
data = r.json()
st = data.get("status",{}) or {}
print(f"5. STATUS: type={st.get('type','?')}, status={st.get('status','?')}, connected={st.get('connected','?')}")

# 6. Wait for data
print("6. Waiting 20s...")
time.sleep(20)

# 7. Check measurements
r = httpx.get(f"{BASE}/api/measurements/latest?limit=100", cookies=c)
measurements = r.json()
pump = [m for m in measurements if "PUMP" in m.get("signal_id","")]
print(f"7. Measurements: total={len(measurements)}, pump={len(pump)}")
for m in pump[:3]:
    print(f"   {m['signal_id']} = {m.get('value','?')} [{m.get('quality','?')}]")

print(f"\nDATA E2E: {'PASS' if pump else 'FAIL'}")
