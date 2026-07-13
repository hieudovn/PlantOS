#!/usr/bin/env python3
"""Test Center Users API + Edge v2 multi-user."""
import httpx, json

BASE = "http://localhost:8000"
EDGE = "http://localhost:8011"

# Test 1: Center Users API
print("=== Test 1: Center Users API ===")
r = httpx.post(f"{BASE}/api/v1/auth/login",
    json={"username": "admin", "password": "PlantOS@2026!"}, timeout=10)
token = r.json().get("access_token", "")
print(f"Login: HTTP {r.status_code}, token={token[:20]}...")

r2 = httpx.get(f"{BASE}/api/v1/users",
    headers={"Authorization": f"Bearer {token}"}, timeout=10)
users = r2.json()
print(f"GET /api/v1/users: HTTP {r2.status_code}, count={len(users)}")
for u in users:
    print(f"  {u['username']}: role={u['role']}, active={u['is_active']}")

# Test 2: Edge Users API
print("\n=== Test 2: Edge Users API ===")
r3 = httpx.get(f"{BASE}/api/v1/edges/EDGEV2-PC-01/users",
    headers={"Authorization": f"Bearer {token}"}, timeout=10)
eu = r3.json()
print(f"GET /edges/EDGEV2-PC-01/users: HTTP {r3.status_code}, count={len(eu)}")
for u in eu:
    print(f"  {u['username']}: role={u['role']}")

# Test 3: Sync
print("\n=== Test 3: Push Sync ===")
r4 = httpx.post(f"{BASE}/api/v1/edges/EDGEV2-PC-01/users/sync",
    headers={"Authorization": f"Bearer {token}"}, timeout=10)
sd = r4.json()
print(f"Sync: HTTP {r4.status_code}, users={len(sd.get('users',[]))}")
for u in sd.get('users', []):
    print(f"  {u['username']}: role={u['role']}, hash={u['password_hash'][:20]}...")

# Test 4: Edge v2 multi-user login
print("\n=== Test 4: Edge v2 Multi-User Login ===")
for username in ["admin", "engineer", "operator"]:
    r = httpx.post(f"{EDGE}/api/auth/login",
        json={"username": username, "password": "PlantOS@2026!"}, timeout=10)
    if r.status_code == 200:
        print(f"  {username}: HTTP {r.status_code} role={r.json().get('role')} display={r.json().get('display_name')}")
    else:
        print(f"  {username}: HTTP {r.status_code}")

print("\n=== ALL TESTS COMPLETE ===")
