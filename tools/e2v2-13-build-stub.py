#!/usr/bin/env python3
"""Write config.ts stub on VPS."""
import subprocess

VPS = "103.97.132.249"
USER = "plantos"

content = '''export function getPlantConfig(plantId: string) { return {}; }
export const config = {};
'''

r = subprocess.run(["ssh", "-o", "StrictHostKeyChecking=no", f"{USER}@{VPS}",
    f"cat > /opt/plantos/frontend/src/features/operations/config.ts << 'STUBEOF'\n{content}STUBEOF"],
    capture_output=True, text=True, timeout=15)
print(r.stdout)
if r.stderr:
    print("ERR:", r.stderr[:200])

# Now build
r = subprocess.run(["ssh", "-o", "StrictHostKeyChecking=no", f"{USER}@{VPS}",
    "cd /opt/plantos/frontend && npx vite build 2>&1 | tail -5"],
    capture_output=True, text=True, timeout=120)
print(r.stdout)
if r.stderr:
    print("ERR:", r.stderr[:200])
