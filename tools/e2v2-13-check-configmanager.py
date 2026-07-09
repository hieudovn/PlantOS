#!/usr/bin/env python3
"""Check ConfigManager to see how it provides config to connectors."""
import subprocess

VPS = "103.97.132.249"
USER = "plantos"

def ssh(cmd):
    r = subprocess.run(["ssh", "-o", "StrictHostKeyChecking=no", f"{USER}@{VPS}", cmd],
                       capture_output=True, text=True, timeout=15)
    return r.stdout.strip()

# Check ConfigManager __init__ and get method
code = ssh("docker exec plantos-edge-v2 grep -n 'def __init__\\|def get\\|class ConfigManager\\|def _load\\|_config' /app/agent/config/__init__.py | head -20")
print("ConfigManager methods:\n", code)

# Check if config is cached 
code2 = ssh("docker exec plantos-edge-v2 grep -n '_config\\|_data\\|cache' /app/agent/config/__init__.py | head -20")
print("\nConfig cache:\n", code2)

# Check what connectors config the registry actually sees
code3 = ssh("""python3 << 'PYEOF'
import yaml
import subprocess as sp
r = sp.run(['docker','exec','plantos-edge-v2','cat','/app/agent/config/config.edge-v2.yaml'], capture_output=True, text=True)
cfg = yaml.safe_load(r.stdout)
conns = cfg.get('connectors', {})
for cid, ccfg in conns.items():
    tags = ccfg.get('tags', [])
    print(f"{cid}: {len(tags)} tags, url={ccfg.get('connection',{}).get('url','?')}")
PYEOF""")
print("\nConnector config parsed from YAML:\n", code3)
