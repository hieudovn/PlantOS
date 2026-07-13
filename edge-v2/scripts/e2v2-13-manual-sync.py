#!/usr/bin/env python3
"""Manual sync users from Center to Edge v2, then test login."""
import httpx, json

BASE = "http://localhost:8000"
EDGE = "http://localhost:8011"

# Login to Center
r = httpx.post(f"{BASE}/api/v1/auth/login",
    json={"username": "admin", "password": "PlantOS@2026!"}, timeout=10)
token = r.json().get("access_token", "")
print(f"Center login: HTTP {r.status_code}")

# Get sync payload
r = httpx.post(f"{BASE}/api/v1/edges/EDGEV2-PC-01/users/sync",
    headers={"Authorization": f"Bearer {token}"}, timeout=10)
data = r.json()
print(f"Center sync: HTTP {r.status_code}, users={len(data.get('users',[]))}")

# Push to edge v2
r2 = httpx.post(f"{EDGE}/api/auth/users/sync", json=data, timeout=10)
print(f"Edge v2 sync: HTTP {r2.status_code}, {r2.text}")

# Test login
print()
for username in ["admin", "engineer", "operator"]:
    r3 = httpx.post(f"{EDGE}/api/auth/login",
        json={"username": username, "password": "PlantOS@2026!"}, timeout=10)
    if r3.status_code == 200:
        j = r3.json()
        print(f"  {username}: HTTP {r3.status_code} role={j.get('role')} display={j.get('display_name')}")
    else:
        print(f"  {username}: HTTP {r3.status_code}")

# Test local user list
r4 = httpx.get(f"{EDGE}/api/auth/users", timeout=10)
print(f"\nEdge v2 local users: {r4.status_code}")
if r4.status_code == 200:
    for u in r4.json():
        print(f"  {u['username']}: role={u['role']} active={u['is_active']}")
