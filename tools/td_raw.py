import subprocess

cmd = "SELECT ts FROM plantos_ts.measurements WHERE signal_id='COMP01-CORE.speed' ORDER BY ts DESC LIMIT 3"
r = subprocess.run(
    ["sudo", "docker", "exec", "plantos-tdengine", "taos", "-s", cmd],
    capture_output=True, text=True, timeout=15
)
print("=== RAW OUTPUT ===")
print(repr(r.stdout[-1000:]))
print("\n=== STDERR ===")
print(repr(r.stderr[-500:]))
