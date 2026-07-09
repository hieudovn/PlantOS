#!/usr/bin/env python3
"""Fix config - update the correct config file that agent actually uses."""
import subprocess, time

VPS = "103.97.132.249"
USER = "plantos"

def ssh(cmd):
    r = subprocess.run(["ssh", "-o", "StrictHostKeyChecking=no", f"{USER}@{VPS}", cmd],
                       capture_output=True, text=True, timeout=15)
    return r.stdout.strip()

# Find the actual config file used
cwd = ssh("docker exec plantos-edge-v2 python3 -c 'import os;print(os.getcwd())'")
print(f"CWD: {cwd}")

# Check expected path
expected = ssh("docker exec plantos-edge-v2 python3 -c 'from pathlib import Path;print(Path(\"edge-v2/agent/config/config.edge-v2.yaml\").resolve())'")
print(f"Expected config path: {expected}")

# Check if it exists
exists = ssh(f"docker exec plantos-edge-v2 ls -la {expected} 2>/dev/null || echo 'NOT FOUND'")
print(f"Exists: {exists}")

# Check both config files
c1 = ssh("docker exec plantos-edge-v2 wc -c /app/agent/config/config.edge-v2.yaml 2>/dev/null || echo 'N/A'")
c2 = ssh(f"docker exec plantos-edge-v2 wc -c {expected} 2>/dev/null || echo 'N/A'")
print(f"\n/app/agent/config/config.edge-v2.yaml: {c1}")
print(f"{expected}: {c2}")

# Copy the 19-tag config to the correct path
print(f"\nCopying config to correct path: {expected}")
ssh(f"docker exec plantos-edge-v2 cp /app/agent/config/config.edge-v2.yaml {expected}")

# Verify
exp = expected
v = ssh(f"docker exec plantos-edge-v2 python3 -c 'import yaml;f=open(\"{exp}\");c=yaml.safe_load(f);wtp=c[\"connectors\"][\"mirror_wtp_signals\"];print(f\"tags={len(wtp.get('tags',[]))} url={wtp.get('connection',{}).get('url','?')}\")'")
print(f"Correct config: {v}")

# Restart v2
print("\nRestarting v2...")
ssh("docker restart plantos-edge-v2")
time.sleep(15)

# Verify
out = ssh("""python3 << 'PYEOF'
import httpx, json
r = httpx.get('http://localhost:8011/api/status', timeout=10)
d = json.loads(r.text)
print(f"status={d['status']} bl={d['sync']['backlog']}")
for c in d['connectors']['list']:
    print(f"  {c['connector_id']}: sig={c['signal_count']} {c['status']} conn={c['connected']}")
PYEOF""")
print(f"\nv2 after restart:\n{out}")
