#!/usr/bin/env python3
"""Phase 8 Runtime Containment — VPS reconnaissance and hardening."""
import subprocess, sys, json

SSH = ["sshpass", "-p", "PlantOS@2026!", "ssh", "-o", "StrictHostKeyChecking=no", "plantos@103.97.132.249"]

def run(cmd):
    result = subprocess.run(SSH + [cmd], capture_output=True, text=True, timeout=60)
    return result.stdout + result.stderr

# 1. Reconnaissance
print("=" * 60)
print("1. SYSTEM INFO")
print(run("uname -a; lsb_release -a 2>/dev/null"))

print("=" * 60)
print("2. DOCKER CONTAINERS")
print(run("docker ps --format '{{.Names}} | {{.Image}} | {{.Ports}} | {{.Status}}'"))

print("=" * 60)
print("3. LISTENING PORTS")
print(run("ss -tlnp 2>/dev/null || netstat -tlnp 2>/dev/null"))

print("=" * 60)
print("4. DOCKER IMAGES")
print(run("docker images --format '{{.Repository}}:{{.Tag}} | {{.ID}} | {{.CreatedAt}}'"))

print("=" * 60)
print("5. DISK & MEMORY")
print(run("df -h /; free -h"))

print("=" * 60)
print("6. FIREWALL")
print(run("sudo ufw status 2>/dev/null || sudo iptables -L -n 2>/dev/null | head -30"))
