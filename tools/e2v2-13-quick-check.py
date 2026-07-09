#!/usr/bin/env python3
"""Simple check of v2 status after force reload."""
import subprocess

VPS = "103.97.132.249"
USER = "plantos"

def ssh(cmd):
    r = subprocess.run(["ssh", "-o", "StrictHostKeyChecking=no", f"{USER}@{VPS}", cmd],
                       capture_output=True, text=True, timeout=15)
    return r.stdout.strip()

# Container status
print("Container:", ssh("docker ps --filter name=plantos-edge --format '{{.Names}} {{.Status}}'"))

# v2 status
out = ssh("""python3 << 'PYEOF'
import httpx, json
r = httpx.get('http://localhost:8011/api/status', timeout=10)
d = json.loads(r.text)
print(f"status={d['status']} bl={d['sync']['backlog']} buf={d['buffer']['row_count']}")
for c in d['connectors']['list']:
    print(f"  {c['connector_id']}: sig={c['signal_count']} {c['status']} conn={c['connected']}")
PYEOF""")
print("v2:", out)

print("v1:", ssh("curl -s -o /dev/null -w '%{http_code}' http://localhost:8001"))
print("sim:", ssh("curl -s http://localhost:9998/ | python3 -c 'import sys,json;d=json.load(sys.stdin);print(len(d))'"))
