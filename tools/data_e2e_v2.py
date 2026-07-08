#!/usr/bin/env python3
"""Data E2E Smoke — v2: add start + status check"""
import httpx, time
BASE = "http://127.0.0.1:8011"

r = httpx.post(f"{BASE}/api/auth/login", json={"username":"admin","password":"Test@1234"})
c = dict(r.cookies)
csrf = c.get("plantos_csrf","")

print("1. Start connector...")
r = httpx.post(f"{BASE}/api/connections/data_e2e_http/start", cookies=c, headers={"X-CSRF-Token": csrf})
print(f"  START: {r.status_code} {r.text[:150]}")

print("2. Check connector status...")
r = httpx.get(f"{BASE}/api/connections/data_e2e_http", cookies=c)
print(f"  STATUS: {r.status_code} {r.text[:200]}")

print("3. Waiting for data collection (15s)...")
time.sleep(15)

print("4. Check local measurements...")
r = httpx.get(f"{BASE}/api/measurements/latest?limit=50", cookies=c)
data = r.json()
pump_signals = [m for m in data if "PUMP" in m.get("signal_id","")]
print(f"  LATEST: {r.status_code}, total={len(data)}, pump_signals={len(pump_signals)}")
for m in pump_signals[:5]:
    print(f"    {m['signal_id']} = {m.get('value','?')} [{m.get('quality','?')}]")

print(f"\nDATA E2E: {'PASS' if pump_signals else 'FAIL — no pump data'}")
