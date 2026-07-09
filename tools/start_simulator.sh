#!/bin/bash
pkill -f http_simulator.py 2>/dev/null
sleep 1
nohup python3 /tmp/http_simulator.py > /tmp/sim.log 2>&1 &
sleep 1
curl -s http://localhost:9998/
echo ""
echo "PID: $(pgrep -f http_simulator.py)"
