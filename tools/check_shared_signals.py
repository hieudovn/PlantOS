#!/usr/bin/env python3
"""Check shared signals between DEMO-PLANT (v1) and EDGEV2-DEMO (v2)."""
import httpx
import os

API = "http://localhost:8000/api/v1"
PW = os.environ.get("PLANTOS_CENTER_PASSWORD", "PlantOS@2026!")

r = httpx.post(f"{API}/auth/login", json={"username": "admin", "password": PW}, timeout=10)
token = r.json().get("access_token", "")
h = {"Authorization": f"Bearer {token}"}

v1 = httpx.get(f"{API}/signals?plant_id=DEMO-PLANT", headers=h, timeout=15).json()
v2 = httpx.get(f"{API}/signals?plant_id=EDGEV2-DEMO", headers=h, timeout=15).json()

v1_data = v1 if isinstance(v1, list) else v1.get("data", [])
v2_data = v2 if isinstance(v2, list) else v2.get("data", [])

v1_ids = {s["signal_id"] for s in v1_data if "signal_id" in s}
v2_ids = {s["signal_id"] for s in v2_data if "signal_id" in s}
shared = sorted(v1_ids & v2_ids)

print(f"v1 (DEMO-PLANT): {len(v1_ids)} signals")
print(f"v2 (EDGEV2-DEMO): {len(v2_ids)} signals")
print(f"Shared: {len(shared)}")
for s in shared:
    print(f"  {s}")

v2_only = sorted(v2_ids - v1_ids)
if v2_only:
    print(f"\nv2-only: {len(v2_only)}")
    for s in v2_only:
        print(f"  {s}")

v1_only = sorted(v1_ids - v2_ids)
if v1_only:
    print(f"\nv1-only: {len(v1_only)}")
    for s in v1_only:
        print(f"  {s}")
