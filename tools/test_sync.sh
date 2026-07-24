#!/bin/bash
# Test user sync endpoint with API key and with admin JWT

API_KEY=$(grep '^API_KEYS=' /opt/plantos/deployment/.env | cut -d= -f2 | cut -d, -f1)

echo "=== 1. Assign user 'engineer' to EDGEV2-PC-01 (via admin JWT) ==="
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"PlantOS@2026!"}' | python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token',''))")

# Assign if not already assigned
curl -s -X POST "http://localhost:8000/api/v1/edges/EDGEV2-PC-01/users" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"user_id":"1"}' 2>&1 | python3 -m json.tool

echo ""
echo "=== 2. Sync users via API key ==="
curl -s -X POST "http://localhost:8000/api/v1/edges/EDGEV2-PC-01/users/sync" \
  -H "X-API-Key: $API_KEY" 2>&1 | python3 -m json.tool

echo ""
echo "=== 3. Sync users via admin JWT ==="
curl -s -X POST "http://localhost:8000/api/v1/edges/EDGEV2-PC-01/users/sync" \
  -H "Authorization: Bearer $TOKEN" 2>&1 | python3 -m json.tool
