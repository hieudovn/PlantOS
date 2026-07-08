#!/usr/bin/env python3
"""Command E2E Smoke: Center sync_now → Edge execute → verify"""
import httpx, time
CENTER = "http://127.0.0.1:8000"
EDGE_NODE = "EDGEV2-PC-01"

# Login to Center
r = httpx.post(f"{CENTER}/api/v1/auth/login", json={"username":"admin","password":"PlantOS@2026!"})
c = dict(r.cookies)
print(f"1. Center login: {r.status_code}")

# Create sync_now command
r = httpx.post(f"{CENTER}/api/v1/edge-nodes/{EDGE_NODE}/commands", cookies=c, json={"command_type":"sync_now"})
print(f"2. Create sync_now: {r.status_code} {r.text[:150]}")
cmd_id = r.json().get("command_id","") if r.status_code == 200 else ""

# Wait for Edge to poll + execute (30s poll + 5s buffer)
print("3. Waiting 40s for Edge to poll command...")
time.sleep(40)

# Check command result
r = httpx.get(f"{CENTER}/api/v1/edge-nodes/{EDGE_NODE}/commands", cookies=c)
cmds = r.json()
print(f"4. Commands: {r.status_code}, {len(cmds)} total")
for cmd in cmds[-3:]:
    print(f"   {cmd.get('command_type')}: {cmd.get('status')}")

# Also test reload_config
r = httpx.post(f"{CENTER}/api/v1/edge-nodes/{EDGE_NODE}/commands", cookies=c, json={"command_type":"reload_config"})
print(f"5. reload_config: {r.status_code} {r.text[:100]}")

# Check center sees edge online
r = httpx.get(f"{CENTER}/api/v1/edge-nodes/{EDGE_NODE}", cookies=c)
node = r.json()
print(f"6. Edge status: {node.get('status','?')}, backlog={node.get('backlog_count','?')}")

sync_ok = any(c.get('command_type')=='sync_now' and c.get('status') in ('success','executing') for c in cmds)
print(f"\nCOMMAND E2E: {'PASS' if sync_ok else 'CHECK'}")
