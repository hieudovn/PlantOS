#!/bin/bash
set -e
echo "=== Creating tables ==="
docker exec plantos-backend python /app/create_tables.py

echo "=== Seeding VF-DEMO ==="
curl -s -X POST http://localhost:8000/api/v1/seed/vf-demo
echo

echo "=== Verifying ==="
curl -s http://localhost:8000/api/v1/plants
echo
curl -s "http://localhost:8000/api/v1/assets?plant_id=VF-DEMO" | python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d.get('value',d)),'assets')"
echo "=== DONE ==="
