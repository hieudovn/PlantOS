#!/usr/bin/env python3
"""Command E2E v2 — use JWT Bearer token"""
import httpx, time, sys
CENTER = "http://127.0.0.1:8000"
EDGE = "EDGEV2-PC-01"

# Login
r = httpx.post(f"{CENTER}/api/v1/auth/login", json={"username":"admin","password":"PlantOS@2026!"})
token = r.headers.get("X-New-Token") or ""
cookies = dict(r.cookies)
print(f"1. Login: {r.status_code}, token={'YES' if token else 'NO'}")

# Try both auth methods
h = {"Authorization": f"Bearer {token}"} if token else {}

# Create sync_now
r = httpx.post(f"{CENTER}/api/v1/edge-nodes/{EDGE}/commands", cookies=cookies, headers=h, json={"command_type":"sync_now"})
print(f"2. sync_now: {r.status_code} {r.text[:120]}")

# If 401, try with API key
if r.status_code == 401:
    r = httpx.post(f"{CENTER}/api/v1/edge-nodes/{EDGE}/commands", 
        headers={"X-API-Key":"plantos-edge-8db46bd13a6a1e50b75f854b"}, json={"command_type":"sync_now"})
    print(f"2b. sync_now (API key): {r.status_code} {r.text[:120]}")

print("3. Waiting 40s...")
time.sleep(40)

# Check commands (try both auth)
r = httpx.get(f"{CENTER}/api/v1/edge-nodes/{EDGE}/commands", cookies=cookies, headers=h)
if r.status_code != 200:
    r = httpx.get(f"{CENTER}/api/v1/edge-nodes/{EDGE}/commands", headers={"X-API-Key":"plantos-edge-8db46bd13a6a1e50b75f854b"})
print(f"4. Commands: {r.status_code}")
data = r.json() if r.status_code == 200 else {}
if isinstance(data, list):
    for cmd in data[-3:]:
        print(f"   {cmd.get('command_type','?')}: {cmd.get('status','?')}")
    sync_ok = any(c.get('command_type')=='sync_now' and c.get('status') in ('success','executing') for c in data)
    print(f"\nCOMMAND E2E: {'PASS' if sync_ok else 'FAIL — no successful sync_now'}")
else:
    print(f"   {r.text[:200]}")
    print("\nCOMMAND E2E: CHECK — API returned non-list")
