#!/bin/bash
# Kill old simulator and start new one with VN timezone
echo "Killing old simulator..."
docker exec plantos-edge-v2 sh -c "kill \$(ps aux | grep wtp_sim | grep -v grep | awk '{print \$1}')" 2>/dev/null
sleep 2

echo "Starting new simulator (VN timezone)..."
docker exec -d plantos-edge-v2 python3 /app/wtp_sim_server.py --port 9998 --interval 5
sleep 3

echo "Verifying timestamp..."
docker exec plantos-edge-v2 python3 << 'PYEOF'
import urllib.request, json
r = urllib.request.urlopen("http://localhost:9998/", timeout=5)
d = json.loads(r.read())
ts = d["timestamp"]
print("Timestamp:", ts)
# Check if it's +07:00
if "+07:00" in ts:
    print("OK - Vietnam timezone (+07:00)")
else:
    print("WARNING - not VN timezone!")
PYEOF
