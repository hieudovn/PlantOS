#!/usr/bin/env python3
"""Build frontend on VPS and capture errors."""
import subprocess

VPS = "103.97.132.249"
USER = "plantos"

r = subprocess.run(["ssh", "-o", "StrictHostKeyChecking=no", f"{USER}@{VPS}",
    "cd /opt/plantos/frontend && npx vite build 2>&1"],
    capture_output=True, text=True, timeout=120)

# Find first error
for line in r.stdout.split('\n'):
    if 'error' in line.lower():
        print(line)
if r.returncode == 0:
    print("BUILD SUCCESS")
else:
    print(f"\nExit code: {r.returncode}")
    # Print last 5 lines
    lines = r.stdout.strip().split('\n')
    for l in lines[-5:]:
        print(l)
