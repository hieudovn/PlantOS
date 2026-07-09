#!/usr/bin/env python3
"""Quick test: login to Center with Python httpx."""
import httpx, os

pw = open('/tmp/pw.txt').read().strip()
print(f"Password len={len(pw)}, first={pw[0]}, last={pw[-1]}")

r = httpx.post("http://localhost:8000/api/v1/auth/login",
    json={"username": "admin", "password": pw}, timeout=10)
print(f"Status: {r.status_code}")
if r.status_code == 200:
    token = r.json().get("access_token","")
    print(f"Token: {token[:20]}...")
    
    # Test measurement fetch
    from datetime import datetime, timezone, timedelta
    to_ts = datetime.now(timezone.utc).isoformat()
    from_ts = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    h = {"Authorization": f"Bearer {token}"}
    r2 = httpx.get(
        f"http://localhost:8000/api/v1/measurements/history?signal_id=PUMP-101.flow_rate&from={from_ts}&to={to_ts}",
        headers=h, timeout=10)
    print(f"Measurement status: {r2.status_code}")
    if r2.status_code == 200:
        data = r2.json()
        pts = data.get("data", []) if isinstance(data, dict) else data
        print(f"Points: {len(pts)}")
        for p in pts[:2]: print(f"  {p}")
else:
    print(f"Response: {r.text[:200]}")
