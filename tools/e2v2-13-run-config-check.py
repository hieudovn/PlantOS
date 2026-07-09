#!/usr/bin/env python3
"""Check both config files."""
import subprocess, sys

VPS = "103.97.132.249"
USER = "plantos"

def ssh(cmd):
    r = subprocess.run(["ssh", "-o", "StrictHostKeyChecking=no", f"{USER}@{VPS}", cmd],
                       capture_output=True, text=True, timeout=15)
    return r.stdout.strip()

# Write a check script to VPS
checker = """#!/usr/bin/env python3
import yaml
for path in ['/app/agent/config/config.edge-v2.yaml', '/app/edge-v2/agent/config/config.edge-v2.yaml']:
    try:
        with open(path) as f:
            c = yaml.safe_load(f)
        wtp = c['connectors']['mirror_wtp_signals']
        print(f"{path}: tags={len(wtp['tags'])} url={wtp['connection']['url']}")
    except Exception as e:
        print(f"{path}: ERROR {e}")

import subprocess as sp
r = sp.run(['docker','inspect','plantos-edge-v2','--format','{{.Config.Cmd}}'], capture_output=True, text=True)
print(f"CMD: {r.stdout.strip()}")

r = sp.run(['docker','inspect','plantos-edge-v2','--format','{{.Config.WorkingDir}}'], capture_output=True, text=True)
print(f"WORKDIR: {r.stdout.strip()}")

import os
print(f"CWD: {os.getcwd()}")
"""

# Write to temp, SCP, and run
with open('d:/Project/Github/PlantOS/edge-v2/scripts/e2v2-13-check-configs.py', 'w') as f:
    f.write(checker)

subprocess.run(["scp", "-o", "StrictHostKeyChecking=no",
    "d:/Project/Github/PlantOS/edge-v2/scripts/e2v2-13-check-configs.py",
    f"{USER}@{VPS}:/tmp/13-check-configs.py"], capture_output=True)

result = ssh("python3 /tmp/13-check-configs.py")
print(result)
