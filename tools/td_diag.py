import subprocess, sys

cmds = [
    "SHOW DATABASES",
    "USE plantos_ts",
    "SHOW STABLES",
    "SELECT COUNT(*) FROM plantos_ts.measurements",
]

for cmd in cmds:
    print(f"\n=== {cmd} ===")
    try:
        r = subprocess.run(
            ["sudo", "docker", "exec", "plantos-tdengine", "taos", "-s", cmd],
            capture_output=True, text=True, timeout=15
        )
        print(r.stdout[-500:] if len(r.stdout) > 500 else r.stdout)
        if r.stderr:
            print("STDERR:", r.stderr[:200])
    except Exception as e:
        print(f"ERROR: {e}")
