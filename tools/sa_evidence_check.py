#!/usr/bin/env python3
"""SA Evidence Script: 5 VPS checks for E2V2-8 gate."""
import subprocess, json, os, sys

SSH = ["ssh", "plantos@103.97.132.249"]
HOME = "/home/plantos"

def ssh(cmd):
    r = subprocess.run(SSH + [cmd], capture_output=True, text=True, timeout=30)
    return r.stdout.strip()

def check(name, cmd, expect=""):
    print(f"\n{'='*50}")
    print(f"CHECK: {name}")
    print(f"{'='*50}")
    out = ssh(cmd)
    print(out[:500])
    if expect and expect in out:
        print(f"✅ PASS: found '{expect}'")
        return True
    elif not expect and out:
        print(f"✅ Output received")
        return True
    else:
        print(f"❌ FAIL")
        return False

results = {}

# 1. Secret scan
print("\n" + "="*60)
print("1. SECRET/CONFIG SCAN")
print("="*60)
scan = ssh(f"grep -rn 'PlantOS@2026' {HOME}/edge-v2/agent/config/ 2>/dev/null || echo CLEAN")
print(f"  Hardcoded passwords: {scan}")
results['1_secret_scan'] = 'CLEAN' in scan

scan2 = ssh(f"grep 'session_secret' {HOME}/edge-v2/agent/config/config.edge-v2.yaml")
print(f"  session_secret: {scan2}")
results['1_session_secret'] = 'CHANGE_ME' in scan2

# 2. Heartbeat + sync
print("\n" + "="*60)
print("2. HEARTBEAT + SYNC")
print("="*60)
status = ssh("curl -s http://localhost:8011/api/status")
try:
    d = json.loads(status)
    rows = d.get("buffer",{}).get("row_count",0)
    backlog = d.get("sync",{}).get("backlog",0)
    print(f"  buffer rows: {rows}, backlog: {backlog}")
    results['2_data_flow'] = rows > 0
except:
    results['2_data_flow'] = False

# 3. Side-by-side comparison
print("\n" + "="*60)
print("3. SIDE-BY-SIDE COMPARISON")
print("="*60)
comp = ssh(f"cd {HOME} && python3 tools/compare_v1_v2_data.py --hours 0.5 --center-url http://localhost:8000 2>&1 | tail -20")
print(comp[:500])
results['3_comparison'] = 'comparison' in comp.lower() or 'shared' in comp.lower()

# 4. Docker container smoke
print("\n" + "="*60)
print("4. DOCKER CONTAINER SMOKE")
print("="*60)
ps_out = ssh("docker ps --filter name=plantos-edge-v2")
print(ps_out[:300])
results['4_docker'] = 'plantos-edge-v2' in ps_out

health = ssh("curl -s http://localhost:8011/api/status")
print(f"  health: {health[:100]}")
results['4_health'] = 'running' in health

# Summary
print("\n" + "="*60)
print("SUMMARY")
print("="*60)
for k, v in results.items():
    print(f"  {k}: {'✅ PASS' if v else '❌ FAIL'}")
