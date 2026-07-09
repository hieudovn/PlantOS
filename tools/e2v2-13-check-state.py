#!/usr/bin/env python3
"""Check state after Tasks 1+2."""
import subprocess, json

VPS = "103.97.132.249"
USER = "plantos"

def ssh(cmd):
    r = subprocess.run(["ssh", "-o", "StrictHostKeyChecking=no", f"{USER}@{VPS}", cmd],
                       capture_output=True, text=True, timeout=30)
    return r.stdout.strip()

print("=== Simulator ===")
sigs = ssh("curl -s http://localhost:9998/ | python3 -c 'import sys,json;d=json.load(sys.stdin);print(len(d))'")
print(f"Signals: {sigs}")

print("\n=== v2 ===")
v2 = ssh("""python3 -c "
import httpx,json
r=httpx.get('http://localhost:8011/api/status',timeout=10)
d=json.loads(r.text)
print(f'status={d[\"status\"]}')
for c in d['connectors']['list']:
    print(f'  {c[\"connector_id\"]}: sig={c[\"signal_count\"]} {c[\"status\"]} conn={c[\"connected\"]}')
" """)
print(v2)

print("\n=== v1 ===")
v1 = ssh("curl -s -o /dev/null -w '%{http_code}' http://localhost:8001")
print(f"v1: {v1}")

print("\n=== Config url ===")
url = ssh("docker exec plantos-edge-v2 cat /app/agent/config/config.edge-v2.yaml | grep 'url:' | head -1")
print(f"Connector URL: {url}")
