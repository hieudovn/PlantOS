#!/usr/bin/env python3
"""Test Edge v2 auth flow."""
import httpx

BASE = "http://127.0.0.1:8011"

# 1. Test first-run setup
print("=== SETUP ===")
r = httpx.post(f"{BASE}/api/auth/setup", json={"password": "Test@1234"})
print(f"Status: {r.status_code} | {r.text[:200]}")

# 2. Test login
print("\n=== LOGIN ===")
r2 = httpx.post(f"{BASE}/api/auth/login", json={"username": "admin", "password": "Test@1234"})
print(f"Status: {r2.status_code} | {r2.text[:200]}")
cookies = dict(r2.cookies)
print(f"Cookies: {list(cookies.keys())}")
csrf = cookies.get("plantos_csrf", "NONE")
print(f"CSRF cookie: {'YES' if csrf != 'NONE' else 'MISSING!'}")

# 3. Test protected endpoint (no auth)
print("\n=== PROTECTED (no auth) ===")
r3 = httpx.get(f"{BASE}/api/config")
print(f"Status: {r3.status_code} (expected 401)")

# 4. Test protected endpoint (with auth)
print("\n=== PROTECTED (with auth) ===")
r4 = httpx.get(f"{BASE}/api/config", cookies=cookies)
print(f"Status: {r4.status_code}")
if r4.status_code == 200:
    data = r4.json()
    key = data.get("api_key", "NOT_FOUND")
    print(f"api_key redacted: {'YES' if key == '***REDACTED***' else f'LEAKED: {key}'}")

# 5. Test logout
print("\n=== LOGOUT ===")
r5 = httpx.post(f"{BASE}/api/auth/logout", cookies=cookies, headers={"X-CSRF-Token": csrf})
print(f"Status: {r5.status_code}")

# 6. Test after logout
print("\n=== AFTER LOGOUT ===")
r6 = httpx.get(f"{BASE}/api/config", cookies=cookies)
print(f"Status: {r6.status_code} (expected 401)")

print("\n=== DONE ===")
