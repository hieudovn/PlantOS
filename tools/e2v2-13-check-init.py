#!/usr/bin/env python3
"""Check how connectors are initialized in main.py."""
import subprocess

VPS = "103.97.132.249"
USER = "plantos"

def ssh(cmd):
    r = subprocess.run(["ssh", "-o", "StrictHostKeyChecking=no", f"{USER}@{VPS}", cmd],
                       capture_output=True, text=True, timeout=15)
    return r.stdout.strip()

# Find connector initialization code
code = ssh("grep -n 'create_connector\\|init_connector\\|load_connector\\|_connectors\\|ConnectorConfig\\|connector_id.*config\\|for.*config' /app/main.py 2>/dev/null | head -30")
print("=== main.py connector init ===")
print(code)

# Also check if there's a config manager that provides config
code2 = ssh("grep -rn 'def.*connector\\|create_connector\\|init_connector' /app/agent/ 2>/dev/null | head -20")
print("\n=== All connector init references ===")
print(code2)

# Check what _create_connectors returns
code3 = ssh("grep -rn '_create_connectors\\|load_connectors\\|init_connectors' /app/agent/ 2>/dev/null | head -20")
print("\n=== Connector loading functions ===")
print(code3)

# Maybe the issue is config_manager.py
code4 = ssh("grep -rn 'connectors' /app/agent/config/ 2>/dev/null | head -20")
print("\n=== Config manager connectors ===")
print(code4)
