#!/usr/bin/env python3
"""Force v2 to reload connector config."""
import subprocess, time, httpx, json

VPS = "103.97.132.249"
USER = "plantos"

def ssh(cmd):
    r = subprocess.run(["ssh", "-o", "StrictHostKeyChecking=no", f"{USER}@{VPS}", cmd],
                       capture_output=True, text=True, timeout=30)
    return r.stdout.strip()

# 1. Verify config has 19 tags
config_tags = ssh("""python3 -c "
import subprocess
r = subprocess.run(['docker','exec','plantos-edge-v2','cat','/app/agent/config/config.edge-v2.yaml'],capture_output=True,text=True,timeout=10)
config = r.stdout
wtp = 0
in_wtp = False
for line in config.split(chr(10)):
    if 'mirror_wtp_signals' in line:
        in_wtp = True
    elif 'mirror_vf_compressor' in line:
        in_wtp = False
    if in_wtp and 'tag_id:' in line:
        wtp += 1
print(f'Tags in config: {wtp}')
" """)
print(config_tags)

# 2. Try reload config via poller
print("\nReloading config via poller...")
subprocess.run(["ssh", "-o", "StrictHostKeyChecking=no", f"{USER}@{VPS}",
    "docker exec plantos-edge-v2 python3 /app/agent/commands/poller.py --action reload_config 2>/dev/null || true"],
    capture_output=True, timeout=15)

time.sleep(5)

# 3. Check connector again
out = ssh("""python3 -c "
import httpx,json
r=httpx.get('http://localhost:8011/api/status',timeout=10)
d=json.loads(r.text)
for c in d['connectors']['list']:
    print(f'{c[\"connector_id\"]}: sig={c[\"signal_count\"]} {c[\"status\"]} conn={c[\"connected\"]}')
" """)
print(f"After reload:\n{out}")

# 4. If still 3, do full restart
if 'sig=3' in out.split('\n')[0]:
    print("\nStill showing 3 — doing full container restart...")
    ssh("docker restart plantos-edge-v2")
    time.sleep(15)
    out2 = ssh("""python3 -c "
import httpx,json
r=httpx.get('http://localhost:8011/api/status',timeout=10)
d=json.loads(r.text)
for c in d['connectors']['list']:
    print(f'{c[\"connector_id\"]}: sig={c[\"signal_count\"]} {c[\"status\"]} conn={c[\"connected\"]}')
" """)
    print(f"After restart:\n{out2}")
