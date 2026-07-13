#!/usr/bin/env python3
"""Check config inside container and test auth."""
import subprocess

VPS = "103.97.132.249"
USER = "plantos"

def ssh(cmd):
    r = subprocess.run(["ssh", "-o", "StrictHostKeyChecking=no", f"{USER}@{VPS}", cmd],
                       capture_output=True, text=True, timeout=15)
    return r.stdout.strip()

# Check mounted config
r = ssh("docker exec plantos-edge-v2 python3 -c 'import yaml;c=yaml.safe_load(open(\"/app/config/config.edge-v2.yaml\"));print(list(c.get(\"auth\",{}).keys()))'")
print(f"Mounted config auth keys: {r}")

# Check PYTHONPATH config path
r = ssh("docker exec plantos-edge-v2 python3 -c 'import os;print(os.environ.get(\"EDGE_CONFIG_PATH\",\"not set\"))'")
print(f"EDGE_CONFIG_PATH: {r}")

# Check the default config path
r = ssh("docker exec plantos-edge-v2 python3 -c 'from pathlib import Path;p=Path(\"edge-v2/agent/config/config.edge-v2.yaml\").resolve();print(f\"Default path: {p}\");print(f\"Exists: {p.exists()}\")' 2>/dev/null")
print(f"Default path check: {r}")

# Check if there's another config file
r = ssh("docker exec plantos-edge-v2 find /app -name \"config.edge-v2.yaml\" 2>/dev/null")
print(f"Config files: {r}")
