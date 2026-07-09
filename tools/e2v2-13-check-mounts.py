#!/usr/bin/env python3
"""Check container mounts."""
import subprocess

VPS = "103.97.132.249"
USER = "plantos"

def ssh(cmd):
    r = subprocess.run(["ssh", "-o", "StrictHostKeyChecking=no", f"{USER}@{VPS}", cmd],
                       capture_output=True, text=True, timeout=15)
    return r.stdout.strip()

mounts = ssh("docker inspect plantos-edge-v2 --format '{{json .Mounts}}'")
print("Mounts:", mounts[:2000])

# Also check if the running process has a different config
print("\n=== Check agent process args ===")
proc = ssh("docker exec plantos-edge-v2 cat /proc/1/cmdline 2>/dev/null | tr '\\0' ' '")
print("Proc cmdline:", proc)

# Check if EDGE_CONFIG_PATH env var exists
print("\n=== Check env ===")
env = ssh("docker exec plantos-edge-v2 env | grep -i config 2>/dev/null || echo 'No config env'")
print(env)
