#!/usr/bin/env python3
import subprocess, json, yaml

for path in ['/app/agent/config/config.edge-v2.yaml', '/app/edge-v2/agent/config/config.edge-v2.yaml']:
    r = subprocess.run(['docker','exec','plantos-edge-v2','cat',path], capture_output=True, text=True, timeout=10)
    if r.returncode == 0:
        c = yaml.safe_load(r.stdout)
        wtp = c['connectors']['mirror_wtp_signals']
        print(f"{path}: tags={len(wtp['tags'])} url={wtp['connection'].get('url','?')}")
    else:
        print(f"{path}: NOT FOUND")

r = subprocess.run(['docker','inspect','plantos-edge-v2','--format','{{.Config.Cmd}}'], capture_output=True, text=True)
print(f"CMD: {r.stdout.strip()}")
r = subprocess.run(['docker','inspect','plantos-edge-v2','--format','{{.Config.WorkingDir}}'], capture_output=True, text=True)
print(f"WORKDIR: {r.stdout.strip()}")

