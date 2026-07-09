#!/usr/bin/env python3
"""Fix config path and restart v2."""
import subprocess, time

VPS = "103.97.132.249"
USER = "plantos"

def ssh(cmd):
    r = subprocess.run(["ssh", "-o", "StrictHostKeyChecking=no", f"{USER}@{VPS}", cmd],
                       capture_output=True, text=True, timeout=30)
    return r.stdout.strip()

# 1. Copy config to correct path
print("Copying config...")
ssh("docker exec plantos-edge-v2 cp /app/agent/config/config.edge-v2.yaml /app/edge-v2/agent/config/config.edge-v2.yaml")
print("OK")

# 2. Verify correct path has 19 tags
v = ssh("docker exec plantos-edge-v2 python3 << 'EOF'\nimport yaml\nwith open('/app/edge-v2/agent/config/config.edge-v2.yaml') as f:\n    c = yaml.safe_load(f)\nwtp = c['connectors']['mirror_wtp_signals']\nprint(f\"tags={len(wtp['tags'])} url={wtp['connection']['url']}\")\nEOF")
print(f"Config: {v}")

# 3. Restart
print("Restarting v2...")
ssh("docker restart plantos-edge-v2")
time.sleep(15)

# 4. Check status
out = ssh("docker exec plantos-edge-v2 python3 << 'EOF'\nimport httpx, json\nr = httpx.get('http://localhost:8011/api/status', timeout=10)\nd = json.loads(r.text)\nprint(f\"status={d['status']}\")\nfor c in d['connectors']['list']:\n    print(f\"  {c['connector_id']}: sig={c['signal_count']} {c['status']} conn={c['connected']}\")\nEOF")
print(f"v2:\n{out}")

# 5. Also check v1
v1 = ssh("curl -s -o /dev/null -w '%{http_code}' http://localhost:8001")
print(f"v1: {v1}")
