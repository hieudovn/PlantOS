#!/bin/bash
kill $(pgrep -f "edge-v2/agent/main.py") 2>/dev/null
sleep 1
cd /home/plantos
PYTHONPATH=/home/plantos nohup python3 edge-v2/agent/main.py --config /home/plantos/edge-v2/agent/config/config.vps.yaml > /tmp/edge-v2.log 2>&1 &
echo "PID: $!"
sleep 5
cat /tmp/edge-v2.log
