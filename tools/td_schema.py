import subprocess

cmds = [
    "DESCRIBE plantos_ts.measurements",
    "SELECT * FROM plantos_ts.measurements WHERE signal_id='COMP01-CORE.speed' LIMIT 2",
    "SELECT * FROM plantos_ts.d_COMP01_CORE_speed LIMIT 2",
]

for cmd in cmds:
    print(f"\n=== {cmd} ===")
    try:
        r = subprocess.run(
            ["sudo", "docker", "exec", "plantos-tdengine", "taos", "-s", cmd],
            capture_output=True, text=True, timeout=15
        )
        print(r.stdout[-800:] if len(r.stdout) > 800 else r.stdout)
        if r.stderr and "Welcome" not in r.stderr:
            print("STDERR:", r.stderr[:300])
    except Exception as e:
        print(f"ERROR: {e}")
