#!/usr/bin/env python3
"""Check v2 connector details."""
import subprocess, json

VPS = "103.97.132.249"
USER = "plantos"

def ssh(cmd):
    r = subprocess.run(["ssh", "-o", "StrictHostKeyChecking=no", f"{USER}@{VPS}", cmd],
                       capture_output=True, text=True, timeout=15)
    return r.stdout.strip()

# Get full status
out = ssh("""python3 -c "
import httpx,json
r=httpx.get('http://localhost:8011/api/status',timeout=10)
d=json.loads(r.text)
print(f'status={d[\"status\"]}')
print(f'bl={d[\"sync\"][\"backlog\"]} buf={d[\"buffer\"][\"row_count\"]}')
for c in d['connectors']['list']:
    print(f'connector: {c[\"connector_id\"]} sig={c[\"signal_count\"]} {c[\"status\"]} conn={c[\"connected\"]}')
" """)
print(out)

# Also check simulator
sigs = ssh("curl -s http://localhost:9998/ | python3 -c 'import sys,json;d=json.load(sys.stdin);print(len(d))'")
print(f"\nSimulator signals: {sigs}")

v1 = ssh("curl -s -o /dev/null -w '%{http_code}' http://localhost:8001")
print(f"v1: {v1}")
