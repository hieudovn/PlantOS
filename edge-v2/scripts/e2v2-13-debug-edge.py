#!/usr/bin/env python3
"""Debug edge users API."""
import httpx, json

BASE = "http://localhost:8000"

# Login
r = httpx.post(f"{BASE}/api/v1/auth/login",
    json={"username": "admin", "password": "PlantOS@2026!"}, timeout=10)
token = r.json().get("access_token", "")
print(f"Login: {r.status_code}")

# Direct test of the endpoint
for path in ["/api/v1/edges/EDGEV2-PC-01/users", "/api/v1/edges/EDGEV2-PC-01/users/export"]:
    r = httpx.get(f"{BASE}{path}", 
        headers={"Authorization": f"Bearer {token}"}, timeout=10)
    print(f"GET {path}: HTTP {r.status_code}")
    print(f"  Response: {r.text[:200]}")
