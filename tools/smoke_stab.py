#!/usr/bin/env python3
"""STAB E2E Smoke Test — runs on VPS."""
import httpx, sys, json
BASE = "http://127.0.0.1:8011"
CENTER = "http://127.0.0.1:8000"
PASS, FAIL = 0, 0

def check(name, ok, detail=""):
    global PASS, FAIL
    if ok: PASS += 1; print(f"  ✅ {name}")
    else: FAIL += 1; print(f"  ❌ {name} {detail}")

# 1. Boot
print("--- 1. Boot Smoke ---")
try:
    r = httpx.get(f"{BASE}/api/status", timeout=5)
    check("GET /api/status", r.status_code == 200, f"got {r.status_code}")
    data = r.json()
    check("status=running", data.get("status") == "running")
    check("node=EDGEV2-PC-01", data.get("edge_node_id") == "EDGEV2-PC-01")
except Exception as e:
    check("Boot", False, str(e))

# 2. Auth
print("\n--- 2. Auth Smoke ---")
try:
    r = httpx.get(f"{BASE}/api/status")
    is_first = r.json().get("first_run", False)
    check("first_run detected", is_first, f"got {r.json()}")
    
    # Reset admin (kill old session)
    with open("/tmp/smoke_cookies.txt", "w") as f: pass
    
    if is_first:
        r = httpx.post(f"{BASE}/api/auth/setup", json={"password": "smoke123"})
        check("setup admin", r.status_code == 200, r.text[:80])
    
    # Login
    r = httpx.post(f"{BASE}/api/auth/login", json={"username": "admin", "password": "smoke123"})
    check("login", r.status_code == 200, r.text[:80])
    csrf = r.cookies.get("plantos_csrf", "")
    check("CSRF cookie", bool(csrf))
    
    # Protected endpoint
    r2 = httpx.get(f"{BASE}/api/config", cookies=dict(r.cookies))
    check("protected /api/config", r2.status_code == 200, f"got {r2.status_code}")
    check("api_key redacted", "REDACTED" in r2.text)
    
    # No auth
    r3 = httpx.get(f"{BASE}/api/config")
    check("no auth → 401", r3.status_code == 401, f"got {r3.status_code}")
except Exception as e:
    check("Auth", False, str(e))

# 3. Center
print("\n--- 3. Center Smoke ---")
try:
    r = httpx.get(f"{CENTER}/api/v1/edge-nodes", headers={"X-API-Key": "plantos-edge-8db46bd13a6a1e50b75f854b"})
    check("Center edge-nodes", r.status_code == 200, f"got {r.status_code}")
    nodes = r.json()
    v2 = [n for n in nodes if n.get("edge_node_id") == "EDGEV2-PC-01"]
    check("EDGEV2-PC-01 in fleet", len(v2) > 0)
    if v2:
        check("EDGEV2-PC-01 online", v2[0].get("status") == "online", str(v2[0]))
except Exception as e:
    check("Center", False, str(e))

# Summary
print(f"\n--- Results: {PASS} passed, {FAIL} failed ---")
sys.exit(0 if FAIL == 0 else 1)
