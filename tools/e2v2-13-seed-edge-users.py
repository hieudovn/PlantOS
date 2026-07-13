#!/usr/bin/env python3
"""Seed edge v2 local user store directly via Center sync export + direct config write."""
import httpx, json, yaml, subprocess, time

VPS = "103.97.132.249"
USER = "plantos"
BASE = "http://localhost:8000"

def ssh(cmd):
    r = subprocess.run(["ssh", "-o", "StrictHostKeyChecking=no", f"{USER}@{VPS}", cmd],
                       capture_output=True, text=True, timeout=30)
    return r.stdout.strip()

# 1. Get users from Center sync
r = httpx.post(f"{BASE}/api/v1/auth/login",
    json={"username": "admin", "password": "PlantOS@2026!"}, timeout=10)
token = r.json().get("access_token", "")

r2 = httpx.post(f"{BASE}/api/v1/edges/EDGEV2-PC-01/users/sync",
    headers={"Authorization": f"Bearer {token}"}, timeout=10)
data = r2.json()
users = data.get("users", [])
print(f"Center sync: {len(users)} users")

# Build config users dict
users_dict = {}
for u in users:
    users_dict[u["username"]] = {
        "password_hash": u["password_hash"],
        "display_name": u["display_name"],
        "role": u["role"],
        "is_active": u.get("is_active", True),
        "synced_at": data.get("synced_at", ""),
    }

# 2. Read current edge v2 config from host
config_yaml = ssh("cat /home/plantos/edge-v2/agent/config/config.edge-v2.yaml")
config = yaml.safe_load(config_yaml)

# 3. Update auth.users and remove legacy admin_hash
config.setdefault("auth", {})["users"] = users_dict
config["auth"].pop("admin_hash", None)

# 4. Write back
new_yaml = yaml.dump(config, default_flow_style=False, indent=2, allow_unicode=True)
# Write via SSH
import tempfile, os
tmp = tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False)
tmp.write(new_yaml)
tmp.close()

subprocess.run(["scp", "-o", "StrictHostKeyChecking=no", tmp.name,
    f"{USER}@{VPS}:/tmp/edge_config_seeded.yaml"], capture_output=True)
os.unlink(tmp.name)

ssh("cp /home/plantos/edge-v2/agent/config/config.edge-v2.yaml /home/plantos/edge-v2/agent/config/config.edge-v2.yaml.bak2")
ssh("cp /tmp/edge_config_seeded.yaml /home/plantos/edge-v2/agent/config/config.edge-v2.yaml")

# Verify
v = ssh("python3 -c \"import yaml;c=yaml.safe_load(open('/home/plantos/edge-v2/agent/config/config.edge-v2.yaml'));print('users='+str(len(c['auth']['users'])),'hash_removed='+str('admin_hash' not in c['auth']))\"")
print(f"Config: {v}")

# 5. Restart edge v2 (config is mounted at /app/config/config.edge-v2.yaml)
# BUT wait - the config volume mount is /home/plantos/edge-v2/agent/config -> /app/config
# The env var EDGE_CONFIG_PATH=/app/config/config.edge-v2.yaml
# So we need to copy to /home/plantos/edge-v2/agent/config/ - which we already did!
# BUT the running agent needs to reload - restart the container
print("Restarting edge v2...")
ssh("docker restart plantos-edge-v2")
time.sleep(15)

# 6. Test multi-user login
print("\n=== Testing multi-user login ===")
for username in ["admin", "engineer", "operator"]:
    r = httpx.post(f"http://{VPS}:8011/api/auth/login",
        json={"username": username, "password": "PlantOS@2026!"}, timeout=10)
    if r.status_code == 200:
        j = r.json()
        print(f"  {username}: HTTP {r.status_code} role={j.get('role')} display={j.get('display_name')}")
    else:
        print(f"  {username}: HTTP {r.status_code}")
