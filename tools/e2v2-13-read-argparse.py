#!/usr/bin/env python3
"""Read the argparse section from main.py."""
import subprocess

VPS = "103.97.132.249"
USER = "plantos"

def ssh(cmd):
    r = subprocess.run(["ssh", "-o", "StrictHostKeyChecking=no", f"{USER}@{VPS}", cmd],
                       capture_output=True, text=True, timeout=15)
    return r.stdout.strip()

code = ssh("docker exec plantos-edge-v2 sed -n '250,280p' /app/agent/main.py")
print(code)
