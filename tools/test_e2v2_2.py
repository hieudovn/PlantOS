#!/usr/bin/env python3
import httpx
BASE = "http://127.0.0.1:8011"

# Login
r = httpx.post(f"{BASE}/api/auth/login", json={"username":"admin","password":"Test@1234"})
c = dict(r.cookies)
print(f"LOGIN: {r.status_code}")

# List connections
r2 = httpx.get(f"{BASE}/api/connections", cookies=c)
print(f"LIST: {r2.status_code} {r2.text[:100]}")

# Create test connector
r3 = httpx.post(f"{BASE}/api/connections", cookies=c, json={
    "connector_id": "test_mqtt_01", "type": "mqtt", "enabled": False,
    "connection": {"broker": "192.168.1.30", "port": 1883}
}, headers={"X-CSRF-Token": c.get("plantos_csrf","")})
print(f"CREATE: {r3.status_code} {r3.text[:150]}")

# Validate
r4 = httpx.post(f"{BASE}/api/connections/test_mqtt_01/validate", cookies=c, json={"type":"mqtt","connection":{"broker":"192.168.1.30","port":1883}}, headers={"X-CSRF-Token": c.get("plantos_csrf","")})
print(f"VALIDATE: {r4.status_code} {r4.text[:100]}")

# Apply draft
r5 = httpx.post(f"{BASE}/api/connections/test_mqtt_01/apply", cookies=c, headers={"X-CSRF-Token": c.get("plantos_csrf","")})
print(f"APPLY: {r5.status_code} {r5.text[:150]}")
