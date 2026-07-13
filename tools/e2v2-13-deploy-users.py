#!/usr/bin/env python3
"""Deploy unified user management to VPS."""
import subprocess, time

VPS = "103.97.132.249"
USER = "plantos"
LOCAL = "d:/Project/Github/PlantOS"

def ssh(cmd):
    r = subprocess.run(["ssh", "-o", "StrictHostKeyChecking=no", f"{USER}@{VPS}", cmd],
                       capture_output=True, text=True, timeout=30)
    out = r.stdout.strip()
    err = r.stderr.strip()
    if r.returncode != 0 and err:
        print(f"  WARN: {err[:200]}")
    return out

def scp(local, remote):
    subprocess.run(["scp", "-o", "StrictHostKeyChecking=no", local, f"{USER}@{VPS}:{remote}"],
                   capture_output=True, timeout=30)
    print(f"  scp {local} -> {remote}")

print("=== PART C: DEPLOY TO VPS ===")

# --- C.1 Backend ---
print("\n1. SCP backend files...")
scp(f"{LOCAL}/backend/app/api/v1.py", "/opt/plantos/backend/app/api/v1.py")
scp(f"{LOCAL}/backend/app/modules/users/__init__.py", "/opt/plantos/backend/app/modules/users/__init__.py")
scp(f"{LOCAL}/backend/app/modules/edge_users/__init__.py", "/opt/plantos/backend/app/modules/edge_users/__init__.py")
scp(f"{LOCAL}/backend/app/modules/edge_users/router.py", "/opt/plantos/backend/app/modules/edge_users/router.py")
scp(f"{LOCAL}/backend/migrations/versions/010_edge_user_assignments.py", "/opt/plantos/backend/migrations/versions/010_edge_user_assignments.py")

print("\n2. Copy into Docker container...")
ssh("docker cp /opt/plantos/backend/app/api/v1.py plantos-backend:/app/app/api/v1.py")
ssh("docker cp /opt/plantos/backend/app/modules/users/__init__.py plantos-backend:/app/app/modules/users/__init__.py")
ssh("docker cp /opt/plantos/backend/app/modules/edge_users/__init__.py plantos-backend:/app/app/modules/edge_users/__init__.py")
ssh("mkdir -p /opt/plantos/backend/app/modules/edge_users")
print("  Creating edge_users dir...")
ssh("docker exec plantos-backend mkdir -p /app/app/modules/edge_users")
ssh("docker cp /opt/plantos/backend/app/modules/edge_users/router.py plantos-backend:/app/app/modules/edge_users/router.py")
ssh("docker cp /opt/plantos/backend/app/modules/edge_users/__init__.py plantos-backend:/app/app/modules/edge_users/__init__.py")
ssh("docker cp /opt/plantos/backend/migrations/versions/010_edge_user_assignments.py plantos-backend:/app/migrations/versions/010_edge_user_assignments.py")

print("\n3. Run migration...")
mig = ssh("docker exec plantos-backend alembic upgrade head")
print(f"  Migration: {mig[:200] if mig else 'OK'}")

print("\n4. Restart backend...")
ssh("docker restart plantos-backend")
time.sleep(5)

# --- C.2 Edge v2 ---
print("\n5. SCP edge-v2 files...")
scp(f"{LOCAL}/edge-v2/agent/auth/local_user_store.py", "/opt/plantos/edge-v2/agent/auth/local_user_store.py")
scp(f"{LOCAL}/edge-v2/agent/auth/auth.py", "/opt/plantos/edge-v2/agent/auth/auth.py")
scp(f"{LOCAL}/edge-v2/agent/web/routes/auth.py", "/opt/plantos/edge-v2/agent/web/routes/auth.py")
scp(f"{LOCAL}/edge-v2/agent/main.py", "/opt/plantos/edge-v2/agent/main.py")

print("\n6. Copy into Docker container...")
ssh("docker cp /opt/plantos/edge-v2/agent/auth/local_user_store.py plantos-edge-v2:/app/agent/auth/local_user_store.py")
ssh("docker cp /opt/plantos/edge-v2/agent/auth/auth.py plantos-edge-v2:/app/agent/auth/auth.py")
ssh("docker cp /opt/plantos/edge-v2/agent/web/routes/auth.py plantos-edge-v2:/app/agent/web/routes/auth.py")
ssh("docker cp /opt/plantos/edge-v2/agent/main.py plantos-edge-v2:/app/agent/main.py")

print("\n7. Restart edge v2...")
ssh("docker restart plantos-edge-v2")
time.sleep(15)

# --- C.3 Test ---
print("\n8. Testing Center Users API...")
result = ssh("""
python3 -c "
import httpx, json, os

# Login
r = httpx.post('http://localhost:8000/api/v1/auth/login',
    json={'username':'admin','password':'PlantOS@2026!'}, timeout=10)
token = r.json().get('access_token','')
print(f'Login: HTTP {r.status_code}')

# Test GET /api/v1/users
r2 = httpx.get('http://localhost:8000/api/v1/users',
    headers={'Authorization': f'Bearer {token}'}, timeout=10)
users = r2.json()
print(f'Users API: HTTP {r2.status_code}, count={len(users)}')
for u in users:
    print(f'  {u[\"username\"]}: role={u[\"role\"]}')

# Test edge users
r3 = httpx.get('http://localhost:8000/api/v1/edges/EDGEV2-PC-01/users',
    headers={'Authorization': f'Bearer {token}'}, timeout=10)
edge_users = r3.json()
print(f'Edge users API: HTTP {r3.status_code}, count={len(edge_users)}')
for u in edge_users:
    print(f'  {u[\"username\"]}: role={u[\"role\"]}')

# Test push sync
r4 = httpx.post('http://localhost:8000/api/v1/edges/EDGEV2-PC-01/users/sync',
    headers={'Authorization': f'Bearer {token}'}, timeout=10)
sync_data = r4.json()
print(f'Sync API: HTTP {r4.status_code}, users={len(sync_data.get(\"users\",[]))}')
"
""")
print(result)

print("\n9. Testing Edge v2 multi-user...")
result2 = ssh("""
python3 -c "
import httpx, json

# Test login as engineer on Edge v2
r = httpx.post('http://localhost:8011/api/auth/login',
    json={'username':'engineer','password':'PlantOS@2026!'}, timeout=10)
print(f'Edge v2 login (engineer): HTTP {r.status_code}')
if r.status_code == 200:
    print(f'  role={r.json().get(\"role\")}')
    print(f'  display_name={r.json().get(\"display_name\")}')

# Test login as admin
r2 = httpx.post('http://localhost:8011/api/auth/login',
    json={'username':'admin','password':'PlantOS@2026!'}, timeout=10)
print(f'Edge v2 login (admin): HTTP {r2.status_code}')
if r2.status_code == 200:
    print(f'  role={r2.json().get(\"role\")}')

# Test login as operator
r3 = httpx.post('http://localhost:8011/api/auth/login',
    json={'username':'operator','password':'PlantOS@2026!'}, timeout=10)
print(f'Edge v2 login (operator): HTTP {r3.status_code}')
if r3.status_code == 200:
    print(f'  role={r3.json().get(\"role\")}')
"
""")
print(result2)

print("\n=== DEPLOYMENT COMPLETE ===")
