#!/usr/bin/env python3
"""Run comparison with correct path /opt/plantos, avoiding bash escaping."""
import os, sys, httpx
from datetime import datetime, timezone, timedelta, timezone

os.chdir("/opt/plantos")
PW = "PlantOS@2026!"
CENTER = "http://localhost:8000"
SIGNALS = ["PUMP-101.flow_rate", "PUMP-101.discharge_pressure", "MOTOR-101.motor_current"]

# Login
r = httpx.post(f"{CENTER}/api/v1/auth/login",
    json={"username": "admin", "password": PW}, timeout=10)
assert r.status_code == 200, f"Login failed: {r.status_code}"
token = r.json()["access_token"]
print(f"Login OK. Token: {token[:20]}...")

# Fetch measurements
h = {"Authorization": f"Bearer {token}"}
now = datetime.now(timezone.utc)
cutoff = now - timedelta(hours=1)
to_ts = now.strftime("%Y-%m-%dT%H:%M:%S")
from_ts = cutoff.strftime("%Y-%m-%dT%H:%M:%S")

print(f"\n{'='*60}")
print(f"Edge v1 vs v2 Data Comparison")
print(f"Time range: {from_ts} → {to_ts}")
print(f"{'='*60}")

results = {}
for sig_id in SIGNALS:
    # Fetch v1 (DEMO-PLANT) and v2 (EDGEV2-DEMO) separately
    for ws in ["DEMO-PLANT", "EDGEV2-DEMO"]:
        key = f"{ws}/{sig_id}"
        url = f"{CENTER}/api/v1/measurements/history?signal_id={sig_id}&from={from_ts}&to={to_ts}"
        r = httpx.get(url, headers=h, timeout=10)
        if r.status_code == 200:
            d = r.json()
            pts = d.get("data", []) if isinstance(d, dict) else d
            values = [float(p.get("value", p.get("val", 0))) for p in pts if p.get("value") is not None]
            results[key] = values
            print(f"  {key}: {len(values)} points")
        else:
            results[key] = []
            print(f"  {key}: HTTP {r.status_code}")

# Compare
print(f"\n{'='*60}")
print("COMPARISON RESULTS")
print(f"{'='*60}")
for sig_id in SIGNALS:
    v1_key = f"DEMO-PLANT/{sig_id}"
    v2_key = f"EDGEV2-DEMO/{sig_id}"
    v1 = results.get(v1_key, [])
    v2 = results.get(v2_key, [])
    if not v1 and not v2:
        print(f"  {sig_id}: SKIP (no data)")
    elif not v1:
        print(f"  {sig_id}: SKIP (no v1 data)")
    elif not v2:
        print(f"  {sig_id}: SKIP (no v2 data)")
    else:
        import statistics
        avg1, avg2 = statistics.mean(v1), statistics.mean(v2)
        diff_pct = abs(avg1 - avg2) / max(abs(avg1), 0.001) * 100
        status = "PASS" if diff_pct <= 5 else "FAIL"
        print(f"  {sig_id}: {status} | v1={len(v1)}pts avg={avg1:.2f} | v2={len(v2)}pts avg={avg2:.2f} | diff={diff_pct:.1f}%")

print("\nDONE")
