#!/bin/bash
# Find what's serving port 9998
PID=865751
echo "=== exe ==="
readlink -f /proc/$PID/exe
echo "=== cmdline ==="
cat /proc/$PID/cmdline | tr '\0' ' '
echo ""
echo "=== cwd ==="
ls -la /proc/$PID/cwd
echo "=== python files in cwd ==="
ls -la /home/plantos/*.py 2>/dev/null
echo "=== systemd service ==="
systemctl status $(systemd-escape --template "$PID") 2>/dev/null || true
