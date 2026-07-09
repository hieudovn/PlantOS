#!/usr/bin/env python3
"""Check http_poll connector code for tag initialization."""
import subprocess

VPS = "103.97.132.249"
USER = "plantos"

def ssh(cmd):
    r = subprocess.run(["ssh", "-o", "StrictHostKeyChecking=no", f"{USER}@{VPS}", cmd],
                       capture_output=True, text=True, timeout=15)
    return r.stdout.strip()

# Check connector code
code = ssh("docker exec plantos-edge-v2 cat /app/agent/connectors/http_poll/connector.py 2>/dev/null | head -80")
print("=== http_poll connector.py (first 80 lines) ===")
print(code)

print("\n=== Check if poll_loop reads config dynamically ===")
code2 = ssh("docker exec plantos-edge-v2 grep -n 'tag_id\\|signal_id\\|signal_count\\|def poll\\|def read_tags\\|self.tags\\|config' /app/agent/connectors/http_poll/connector.py 2>/dev/null | head -30")
print(code2)

print("\n=== How does main.py load connectors? ===")
main = ssh("grep -n 'connector\\|http_poll\\|load_config\\|init_connector' /app/agent/main.py 2>/dev/null | head -20")
print(main)
