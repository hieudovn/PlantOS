#!/usr/bin/env python3
"""Deep check v2 state."""
import subprocess

VPS = "103.97.132.249"
USER = "plantos"

def ssh(cmd):
    r = subprocess.run(["ssh", "-o", "StrictHostKeyChecking=no", f"{USER}@{VPS}", cmd],
                       capture_output=True, text=True, timeout=30)
    return r.stdout.strip(), r.stderr.strip()

# Container status
out, err = ssh("docker ps --filter name=plantos-edge --format '{{.Names}} {{.Status}}'")
print(f"Container: {out}")

# Config check
out, err = ssh("docker exec plantos-edge-v2 cat /app/agent/config/config.edge-v2.yaml 2>/dev/null | head -40")
if err and "Error" in err:
    print(f"Config error: {err}")
    # Container might not be running
    out2, _ = ssh("docker ps -a --filter name=plantos-edge --format '{{.Names}} {{.Status}}'")
    print(f"All containers: {out2}")
else:
    print(f"Config (first 40 lines):\n{out[:1000]}")

# Try direct v2 status
out, err = ssh("curl -s http://localhost:8011/api/status 2>/dev/null | head -c 200")
print(f"\nv2 status response: '{out}'")
