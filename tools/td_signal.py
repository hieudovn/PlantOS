import subprocess

cmds = [
    "SELECT COUNT(*) FROM plantos_ts.measurements WHERE signal_id='COMP01-CORE.speed'",
    "SELECT ts, value FROM plantos_ts.measurements WHERE signal_id='COMP01-CORE.speed' ORDER BY ts DESC LIMIT 3",
    "SELECT ts, value FROM plantos_ts.measurements WHERE signal_id='COMP01-CORE.speed' ORDER BY ts ASC LIMIT 3",
    "SELECT MIN(ts), MAX(ts) FROM plantos_ts.measurements WHERE signal_id='COMP01-CORE.speed'",
]

for cmd in cmds:
    print(f"\n=== {cmd} ===")
    try:
        r = subprocess.run(
            ["sudo", "docker", "exec", "plantos-tdengine", "taos", "-s", cmd],
            capture_output=True, text=True, timeout=15
        )
        # Extract just the data lines
        for line in r.stdout.split("\n"):
            if "|" in line and "===" not in line and "row" not in line.lower() and "taos" not in line.lower() and "Welcome" not in line and "Copyright" not in line:
                line = line.strip()
                if line:
                    print(line)
    except Exception as e:
        print(f"ERROR: {e}")
