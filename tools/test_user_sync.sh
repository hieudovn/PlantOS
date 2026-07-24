#!/bin/bash
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"PlantOS@2026!"}' | python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token',''))")

echo "Token: ${TOKEN:0:20}..."

# Test the sync endpoint
echo "=== User Sync Endpoint ==="
curl -s -X POST "http://localhost:8000/api/v1/edges/EDGEV2-PC-01/users/sync" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

echo ""
echo "=== Assign user to edge ==="
curl -s -X POST "http://localhost:8000/api/v1/edges/EDGEV2-PC-01/users" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"user_id":"1"}' 2>&1 | python3 -m json.tool

echo ""
echo "=== User Sync after assignment ==="
curl -s -X POST "http://localhost:8000/api/v1/edges/EDGEV2-PC-01/users/sync" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
