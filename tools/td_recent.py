import subprocess

# Check latest timestamps for COMP01-CORE.speed
cmd = "SELECT ts, value FROM plantos_ts.measurements WHERE signal_id='COMP01-CORE.speed' ORDER BY ts DESC LIMIT 5"
print(f"=== {cmd} ===")
r = subprocess.run(
    ["sudo", "docker", "exec", "plantos-tdengine", "taos", "-s", cmd],
    capture_output=True, text=True, timeout=15
)
print(r.stdout)

# Also count data in last 2 hours
cmd2 = "SELECT COUNT(*) FROM plantos_ts.measurements WHERE signal_id='COMP01-CORE.speed' AND ts >= NOW - 2h"
print(f"\n=== {cmd2} ===")
r2 = subprocess.run(
    ["sudo", "docker", "exec", "plantos-tdengine", "taos", "-s", cmd2],
    capture_output=True, text=True, timeout=15
)
print(r2.stdout)
