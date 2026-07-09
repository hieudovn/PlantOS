#!/usr/bin/env python3
"""Check v2 agent structure inside container."""
import subprocess

VPS = "103.97.132.249"
USER = "plantos"

def ssh(cmd):
    r = subprocess.run(["ssh", "-o", "StrictHostKeyChecking=no", f"{USER}@{VPS}", cmd],
                       capture_output=True, text=True, timeout=15)
    return r.stdout.strip()

code = ssh("docker exec plantos-edge-v2 find /app -name '*.py' -path '*/main*' -o -name '*.py' -path '*/agent*' 2>/dev/null | head -20")
print("Python files:\n", code)

print("\n=== Main entry ===")
code2 = ssh("docker exec plantos-edge-v2 python3 -c 'import agent.main; print(agent.main.__file__)' 2>/dev/null || echo 'Cannot import'")
print(code2)

print("\n=== agent directory ===")
code3 = ssh("docker exec plantos-edge-v2 ls -la /app/agent/ 2>/dev/null")
print(code3)
