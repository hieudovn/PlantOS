#!/bin/bash
set -e

echo "=== Login test ==="
RESP=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"PlantOS@2026"}')
echo "Response: $RESP" | head -c 200

TOKEN=$(echo "$RESP" | python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token',''))" 2>/dev/null)
echo "Token length: ${#TOKEN}"

if [ -n "$TOKEN" ]; then
  echo "=== Testing with token ==="
  curl -s -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/plants
else
  echo "=== Login may need different password ==="
  echo "Trying common passwords..."
  for pw in "PlantOS@2026" "admin" "plantos" "PlantOS2026"; do
    CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:8000/api/v1/auth/login \
      -H "Content-Type: application/json" \
      -d "{\"username\":\"admin\",\"password\":\"$pw\"}")
    echo "  password='$pw': HTTP $CODE"
  done
fi
