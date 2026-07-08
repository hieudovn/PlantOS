#!/bin/bash
# EV2-STAB: Clear All 3 SA Gates
# Run on VPS: bash /tmp/clear_gates.sh
set -e
echo "=== Gate 1: Data E2E ==="
python3 /tmp/data_e2e_v2.py
echo ""

echo "=== Gate 2: Command E2E ==="
# Deploy backend fix first
echo "PlantOS@2026!" | sudo -S docker cp /home/plantos/cf0-fix/router.py plantos-backend:/app/app/modules/edge_nodes/router.py
echo "PlantOS@2026!" | sudo -S docker cp /home/plantos/cf0-fix/commands.py plantos-backend:/app/app/modules/edge_nodes/commands.py
echo "PlantOS@2026!" | sudo -S docker restart plantos-backend
sleep 5
python3 /tmp/command_e2e.py
echo ""

echo "=== Gate 3: Docker Smoke ==="
cd /home/plantos/edge-v2
echo "PlantOS@2026!" | sudo -S docker compose -f docker-compose.edge-v2.yml down 2>/dev/null || true
echo "PlantOS@2026!" | sudo -S docker compose -f docker-compose.edge-v2.yml build
echo "PlantOS@2026!" | sudo -S docker compose -f docker-compose.edge-v2.yml up -d
sleep 8
curl -s http://localhost:8011/api/status | python3 -m json.tool
curl -s http://localhost:8011/api/version
echo ""
echo "=== ALL GATES COMPLETE ==="
