#!/usr/bin/env python3
"""Get full connector status from API."""
import subprocess, json

VPS = "103.97.132.249"
USER = "plantos"

def ssh(cmd):
    r = subprocess.run(["ssh", "-o", "StrictHostKeyChecking=no", f"{USER}@{VPS}", cmd],
                       capture_output=True, text=True, timeout=15)
    return r.stdout.strip()

# Get full API response
result = ssh("docker exec plantos-edge-v2 python3 -c "
    "'import httpx, json; "
    "r = httpx.get(\"http://localhost:8011/api/status\", timeout=10); "
    "d = json.loads(r.text); "
    "print(json.dumps(d[\"connectors\"], indent=2))'")
print(result)
