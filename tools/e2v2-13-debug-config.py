#!/usr/bin/env python3
"""Dig deeper into config loading."""
import subprocess

VPS = "103.97.132.249"
USER = "plantos"

def ssh(cmd):
    r = subprocess.run(["ssh", "-o", "StrictHostKeyChecking=no", f"{USER}@{VPS}", cmd],
                       capture_output=True, text=True, timeout=15)
    return r.stdout.strip()

# Check where ConfigManager reads from
code = ssh("docker exec plantos-edge-v2 grep -A10 'def __init__' /app/agent/config/__init__.py")
print("ConfigManager.__init__:\n", code)

print("\n=== Check config file location ===")
code2 = ssh("docker exec plantos-edge-v2 ls -la /app/agent/config/config.edge-v2.yaml /app/config/config.edge-v2.yaml /app/edge-v2/agent/config/config.edge-v2.yaml 2>/dev/null")
print(code2)

print("\n=== Check which config file main.py uses ===")
code3 = ssh("docker exec plantos-edge-v2 grep -n 'config_path\\|config\\|ConfigManager' /app/agent/main.py | head -10")
print(code3)

print("\n=== Check the actual in-memory config via API ===")
# Let's restart v2 and check if it picks up
out = ssh("docker exec plantos-edge-v2 python3 -c 'import yaml;f=open(\"/app/agent/config/config.edge-v2.yaml\");c=yaml.safe_load(f);conns=c.get(\"connectors\",{});wtp=conns.get(\"mirror_wtp_signals\",{});print(f\"tags: {len(wtp.get(\\\"tags\\\",[]))}, url: {wtp.get(\\\"connection\\\",{}).get(\\\"url\\\",\\\"?\\\")}\")'")
print("\nParsed from file:", out)
