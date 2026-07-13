#!/usr/bin/env python3
"""Build frontend and capture full error."""
import subprocess

VPS = "103.97.132.249"
USER = "plantos"

r = subprocess.run(["ssh", "-o", "StrictHostKeyChecking=no", f"{USER}@{VPS}",
    "cd /opt/plantos/frontend && npx vite build 2>&1"],
    capture_output=True, text=True, timeout=120)

output = r.stdout

# Find the actual error lines (not stack trace)
lines = output.split('\n')
for i, line in enumerate(lines):
    if 'error' in line.lower() and 'rollup' not in line.lower() and 'Error:' not in line:
        # Print this line and the one before it
        if i > 0:
            print(lines[i-1])
        print(line)
        print("---")

if r.returncode == 0:
    print("BUILD SUCCESS")
else:
    print(f"\nExit code: {r.returncode}")
    # Print context around first error
    for i, line in enumerate(lines[:30]):
        print(line)
