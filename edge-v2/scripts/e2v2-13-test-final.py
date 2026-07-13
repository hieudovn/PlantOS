#!/usr/bin/env python3
"""Test edge v2 multi-user login."""
import httpx

EDGE = "http://localhost:8011"

print("=== Edge v2 Multi-User ===")
for username in ["admin", "engineer", "operator"]:
    r = httpx.post(f"{EDGE}/api/auth/login",
        json={"username": username, "password": "PlantOS@2026!"}, timeout=10)
    if r.status_code == 200:
        j = r.json()
        print(f"  {username}: HTTP {r.status_code} role={j.get('role')} display={j.get('display_name')}")
    else:
        print(f"  {username}: HTTP {r.status_code}")
