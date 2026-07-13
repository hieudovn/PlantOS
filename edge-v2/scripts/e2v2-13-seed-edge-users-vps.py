#!/usr/bin/env python3
"""Seed edge v2 local user store directly via config update."""
import yaml, subprocess, time, httpx, json

def r(cmd):
    return subprocess.run(cmd, capture_output=True, text=True, timeout=30).stdout.strip()

# 1. Get users from Center
r0 = httpx.post("http://localhost:8000/api/v1/auth/login",
    json={"username": "admin", "password": "PlantOS@2026!"}, timeout=10)
token = r0.json().get("access_token", "")

r1 = httpx.post("http://localhost:8000/api/v1/edges/EDGEV2-PC-01/users/sync",
    headers={"Authorization": f"Bearer {token}"}, timeout=10)
data = r1.json()
users = data.get("users", [])
print(f"Center: {len(users)} users")

# 2. Read and update config
with open("/home/plantos/edge-v2/agent/config/config.edge-v2.yaml") as f:
    config = yaml.safe_load(f)

users_dict = {}
for u in users:
    users_dict[u["username"]] = {
        "password_hash": u["password_hash"],
        "display_name": u["display_name"],
        "role": u["role"],
        "is_active": u.get("is_active", True),
        "synced_at": data.get("synced_at", ""),
    }
config.setdefault("auth", {})["users"] = users_dict
config["auth"].pop("admin_hash", None)

with open("/home/plantos/edge-v2/agent/config/config.edge-v2.yaml", "w") as f:
    yaml.dump(config, f, default_flow_style=False, indent=2, allow_unicode=True)
print(f"Config: users={len(users_dict)}, hash_removed=True")

# 3. Restart
print("Restarting edge v2...")
r(["docker", "restart", "plantos-edge-v2"])
time.sleep(15)

# 4. Test
print("\n=== Multi-user login test ===")
for u in ["admin", "engineer", "operator"]:
    r2 = httpx.post("http://localhost:8011/api/auth/login",
        json={"username": u, "password": "PlantOS@2026!"}, timeout=10)
    if r2.status_code == 200:
        j = r2.json()
        print(f"  {u}: HTTP {r2.status_code} role={j.get('role')} display={j.get('display_name')}")
    else:
        print(f"  {u}: HTTP {r2.status_code}")
