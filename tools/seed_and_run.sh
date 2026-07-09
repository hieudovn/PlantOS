#!/bin/bash
# Run seed scripts and comparison on VPS
set -e
cd /home/plantos

echo "=== Getting auth token ==="
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"PlantOS@2026"}' | \
  python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token',''))")
echo "Token obtained: ${TOKEN:0:10}..."

echo "=== Seeding DEMO-PLANT ==="
python3 scripts/seed_demo_plant.py --api-url http://localhost:8000

echo "=== Seeding EDGEV2-DEMO ==="
python3 scripts/seed_edgev2_demo.py --api-url http://localhost:8000

echo "=== Verifying plants ==="
curl -s -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/plants | \
  python3 -c "import sys,json; [print('  '+p['plant_id']) for p in json.load(sys.stdin)]"

echo "=== Running comparison tool ==="
python3 tools/compare_v1_v2_data.py --center-url http://localhost:8000 2>&1 || true

echo "=== Running migration dry-run ==="
python3 tools/migrate_v1_config_to_v2.py edge/agent/config.yaml --dry-run 2>&1 | head -20
echo "..."
python3 tools/migrate_v1_config_to_v2.py edge/agent/config.yaml --dry-run 2>&1 | tail -10

echo "=== Edge v2 status ==="
curl -s http://localhost:8011/api/status | python3 -c "
import sys,json
d=json.load(sys.stdin)
print('rows={}, backlog={}'.format(d.get('buffer',{}).get('row_count',0), d.get('sync',{}).get('backlog',0)))
print('connectors: {} active'.format(d.get('connectors',{}).get('active',0)))
"

echo "=== Edge v1 status ==="
curl -s -o /dev/null -w "HTTP %{http_code}\n" http://localhost:8001

echo "=== Docker ==="
docker ps --format "table {{.Names}}\t{{.Status}}"

echo "=== DONE ==="
