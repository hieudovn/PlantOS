#!/usr/bin/env python3
"""E2V2-10 Task 4: Rollback — stop v2, verify v1, restore v2."""
import subprocess
import sys

VPS = "103.97.132.249"
USER = "plantos"
SSH = ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=10",
       f"{USER}@{VPS}"]


def run(cmd: str) -> str:
    full_cmd = SSH + [cmd]
    r = subprocess.run(full_cmd, capture_output=True, text=True, timeout=30)
    if r.returncode != 0:
        print(f"  WARN: exit={r.returncode}, stderr={r.stderr[:200]}")
    return r.stdout.strip()


print("=== E2V2-10 TASK 4: ROLLBACK ===")

# Step 1: Stop v2
print("\nStopping plantos-edge-v2...")
out = run("docker stop plantos-edge-v2")
print(f"  {out}")

# Step 2: Verify v1
v1 = run("curl -s -o /dev/null -w '%{http_code}' http://localhost:8001")
print(f"v1 after v2 stop: {v1}")

# Step 3: Verify v1 heartbeat
print("\nEdge nodes after v2 stop:")
out = run("""python3 -c "
import httpx, json
resp = httpx.get('http://localhost:8000/api/v1/edge-nodes', timeout=10)
for n in resp.json():
    print(f'  {n[\"edge_node_id\"]}: {n.get(\"status\",\"?\")}')
" """)
print(out)

# Step 4: Verify v1 data flow
print("\nv1 measurements after rollback:")
out = run("""python3 -c "
import httpx, json
resp = httpx.get('http://localhost:8000/api/v1/measurements/history?plant_id=DEMO-PLANT&limit=3', timeout=10)
print(f'  {len(resp.json())} points')
" """)
print(out)

# Step 5: Restart v2
print("\nRestarting v2 in mirror mode...")
out = run("docker start plantos-edge-v2")
print(f"  {out}")

import time
time.sleep(10)

v2 = run("""python3 -c "
import httpx, json
resp = httpx.get('http://localhost:8011/api/status', timeout=10)
print(json.loads(resp.text).get('status','?'))
" """)
print(f"v2 after restart: {v2}")

# Final state
print("\n=== FINAL STATE ===")
v1f = run("curl -s -o /dev/null -w '%{http_code}' http://localhost:8001")
v2f = run("""python3 -c "
import httpx, json
resp = httpx.get('http://localhost:8011/api/status', timeout=10)
print(json.loads(resp.text).get('status','?'))
" """)
cf = run("curl -s -o /dev/null -w '%{http_code}' http://localhost:8000/health")
bl = run("""python3 -c "
import httpx, json
resp = httpx.get('http://localhost:8011/api/status', timeout=10)
print(json.loads(resp.text).get('sync',{}).get('backlog','?'))
" """)
print(f"v1: {v1f}")
print(f"v2: {v2f}")
print(f"Center: {cf}")
print(f"Backlog: {bl}")

print("\n=== DRY-RUN COMPLETE ===")
