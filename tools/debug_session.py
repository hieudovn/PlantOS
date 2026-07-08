#!/usr/bin/env python3
"""Debug session validation — print cookie values."""
import httpx
import json

BASE = "http://127.0.0.1:8011"

# Setup
print("=== SETUP ===")
r = httpx.post(f"{BASE}/api/auth/setup", json={"password": "Test@1234"})
print(f"Setup: {r.status_code}")

# Login and print cookies
print("\n=== LOGIN ===")
r2 = httpx.post(f"{BASE}/api/auth/login", json={"username": "admin", "password": "Test@1234"})
print(f"Login: {r2.status_code}")

# Print raw Set-Cookie headers
for name, value in r2.headers.multi_items():
    if 'cookie' in name.lower() or 'set-' in name.lower():
        print(f"  Header: {name}: {value[:100]}")

# Print extracted cookies
for name, cookie in r2.cookies.items():
    print(f"  Cookie: {name} = {cookie[:80]}...")

# Try accessing protected endpoint with raw cookie header
cookie_header = "; ".join(f"{name}={value}" for name, value in r2.cookies.items())
print(f"\n=== Cookie header: {cookie_header[:120]}...")

# Test with raw headers
r3 = httpx.get(f"{BASE}/api/config", headers={"Cookie": cookie_header})
print(f"\nProtected (raw cookie): {r3.status_code}")

if r3.status_code == 401:
    # Try to parse the session cookie value 
    session_val = r2.cookies.get("plantos_session", "")
    if ":" in session_val:
        sig, payload = session_val.split(":", 1)
        print(f"Session sig: {sig}")
        print(f"Session payload: {payload[:100]}")
        try:
            data = json.loads(payload)
            print(f"Parsed: {data}")
        except Exception as e:
            print(f"JSON parse error: {e}")
