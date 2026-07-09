#!/usr/bin/env python3
"""Check what config path v2 agent actually uses."""
import subprocess

VPS = "103.97.132.249"
USER = "plantos"

def ssh(cmd):
    r = subprocess.run(["ssh", "-o", "StrictHostKeyChecking=no", f"{USER}@{VPS}", cmd],
                       capture_output=True, text=True, timeout=15)
    return r.stdout.strip()

# Check env vars
env = ssh("docker inspect plantos-edge-v2 --format '{{json .Config.Env}}'")
print("All env vars:")
print(env[:2000])

# Check where the config was actually loaded from
print("\n=== Checking config loading ===")
# The ConnectorRegistry.start_all uses self.config.get("connectors",{})
# self.config is ConfigManager which loads from config_path
# Let's check what ConfigManager._data contains
print(ssh("docker exec plantos-edge-v2 python3 -c "
    "import yaml; "
    "from agent.config import ConfigManager; "
    "cm = ConfigManager.__new__(ConfigManager); "
    "cm.__init__(); print('OK')" 2>/dev/null || echo 'Not importable'))

# Just check the process command line
print("\n=== Process info ===")
print(ssh("docker exec plantos-edge-v2 cat /proc/1/cmdline 2>/dev/null | tr '\\0' ' '"))
