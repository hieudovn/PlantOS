#!/usr/bin/env python3
"""Check ConnectorRegistry code."""
import subprocess

VPS = "103.97.132.249"
USER = "plantos"

def ssh(cmd):
    r = subprocess.run(["ssh", "-o", "StrictHostKeyChecking=no", f"{USER}@{VPS}", cmd],
                       capture_output=True, text=True, timeout=15)
    return r.stdout.strip()

code = ssh("docker exec plantos-edge-v2 cat /app/agent/connectors/__init__.py")
print(code)
