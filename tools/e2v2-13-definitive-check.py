#!/usr/bin/env python3
"""Definitive check - which config file does the agent use."""
import subprocess

VPS = "103.97.132.249"
USER = "plantos"

def ssh(cmd):
    r = subprocess.run(["ssh", "-o", "StrictHostKeyChecking=no", f"{USER}@{VPS}", cmd],
                       capture_output=True, text=True, timeout=15)
    return r.stdout.strip()

# Check BOTH config files
print("=== /app/agent/config/config.edge-v2.yaml ===")
print(ssh("docker exec plantos-edge-v2 python3 -c "
    "import yaml;f=open('/app/agent/config/config.edge-v2.yaml');c=yaml.safe_load(f);"
    "wtp=c['connectors']['mirror_wtp_signals'];"
    "print('tags='+str(len(wtp['tags']))+' url='+wtp['connection']['url'])"))

print("\n=== /app/edge-v2/agent/config/config.edge-v2.yaml ===")
print(ssh("docker exec plantos-edge-v2 python3 -c "
    "import yaml;f=open('/app/edge-v2/agent/config/config.edge-v2.yaml');c=yaml.safe_load(f);"
    "wtp=c['connectors']['mirror_wtp_signals'];"
    "print('tags='+str(len(wtp['tags']))+' url='+wtp['connection']['url'])"))

# Check what CMD the container uses
print("\n=== Docker CMD ===")
print(ssh("docker inspect plantos-edge-v2 --format '{{json .Config.Cmd}}'"))

# Check WORKDIR
print("\n=== WORKDIR ===")
print(ssh("docker inspect plantos-edge-v2 --format '{{json .Config.WorkingDir}}'"))

# Check what python thinks is the path
print("\n=== Python CWD ===")
print(ssh("docker exec plantos-edge-v2 python3 -c 'import os;print(os.getcwd())'"))
