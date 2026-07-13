#!/usr/bin/env python3
"""Manual sync with proper auth - get cookie first."""
import httpx, json

EDGE = "http://localhost:8011"
BASE = "http://localhost:8000"

# Step 1: Login to Edge v2 as admin to get session cookie
r = httpx.post(f"{EDGE}/api/auth/login",
    json={"username": "admin", "password": "PlantOS@2026!"}, timeout=10)
print(f"Edge admin login: HTTP {r.status_code}")
if r.status_code != 200:
    exit(1)

# Get session cookie
cookie = r.cookies.get("plantos_session")
csrf = r.cookies.get("plantos_csrf")
print(f"Session: {cookie[:30]}...")
print(f"CSRF: {csrf}")

# Step 2: Get users from Center sync
r2 = httpx.post(f"{BASE}/api/v1/auth/login",
    json={"username": "admin", "password": "PlantOS@2026!"}, timeout=10)
token = r2.json().get("access_token", "")

r3 = httpx.post(f"{BASE}/api/v1/edges/EDGEV2-PC-01/users/sync",
    headers={"Authorization": f"Bearer {token}"}, timeout=10)
data = r3.json()
print(f"Center has {len(data.get('users',[]))} users")

# Step 3: Sync to Edge v2 with CSRF token
r4 = httpx.post(f"{EDGE}/api/auth/users/sync",
    json=data,
    cookies={"plantos_session": cookie, "plantos_csrf": csrf},
    headers={"X-CSRF-Token": csrf},
    timeout=10)
print(f"Edge v2 sync: HTTP {r4.status_code}, {r4.text}")

# Step 4: Test login
print()
for username in ["admin", "engineer", "operator"]:
    r5 = httpx.post(f"{EDGE}/api/auth/login",
        json={"username": username, "password": "PlantOS@2026!"}, timeout=10)
    if r5.status_code == 200:
        j = r5.json()
        print(f"  {username}: HTTP {r5.status_code} role={j.get('role')} display={j.get('display_name')}")
    else:
        print(f"  {username}: HTTP {r5.status_code}")
