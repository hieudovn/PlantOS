#!/usr/bin/env python3
"""Find how config_path is set in main.py."""
import subprocess

VPS = "103.97.132.249"
USER = "plantos"

def ssh(cmd):
    r = subprocess.run(["ssh", "-o", "StrictHostKeyChecking=no", f"{USER}@{VPS}", cmd],
                       capture_output=True, text=True, timeout=15)
    return r.stdout.strip()

# Find where EdgeAgentV2 is instantiated and what config_path is passed
code = ssh("docker exec plantos-edge-v2 grep -n 'EdgeAgentV2\\|config_path\\|--config\\|argparse' /app/agent/main.py | head -30")
print("Config path in main.py:\n", code)

# Show the argparse section
code2 = ssh("docker exec plantos-edge-v2 sed -n '120,180p' /app/agent/main.py")
print("\nArgparse section:\n", code2)

# Check the docker entrypoint
code3 = ssh("docker inspect plantos-edge-v2 --format '{{json .Config.Cmd}}' 2>/dev/null")
print("\nDocker CMD:\n", code3)

# Also check docker-compose or Dockerfile for how it's started
code4 = ssh("docker inspect plantos-edge-v2 --format '{{json .Args}}' 2>/dev/null")
print("\nDocker Args:\n", code4)
