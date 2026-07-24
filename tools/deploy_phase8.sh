#!/bin/bash
set -e
RELEASE_SHA=f7d77cf
RELEASE_SHORT=${RELEASE_SHA:0:7}

echo "=== Step 1: Checkout Phase 8 code ==="
cd /opt/plantos
git fetch origin phase8-closure
git stash --include-untracked 2>/dev/null || true
git checkout -f --detach "$RELEASE_SHA"
CURRENT=$(git rev-parse --short=7 HEAD)
echo "CHECKOUT_OK: $CURRENT"

echo "=== Step 2: Build backend ==="
TIMESTAMP=$(date -u +%Y%m%dT%H%M%SZ)
docker build \
  --label "org.opencontainers.image.revision=$RELEASE_SHA" \
  --label "org.opencontainers.image.created=$TIMESTAMP" \
  --label "org.opencontainers.image.version=phase8-$RELEASE_SHORT" \
  -t "plantos-backend:$RELEASE_SHORT" \
  -f backend/Dockerfile \
  backend 2>&1 | tail -5

echo "=== Step 3: Backup and swap ==="
docker tag deployment-backend:latest deployment-backend:backup 2>/dev/null || true
docker stop plantos-backend 2>/dev/null || true
docker rm plantos-backend 2>/dev/null || true

echo "=== Step 4: Start new backend ==="
docker run -d --name plantos-backend \
  --network deployment_plantos-net \
  -p 127.0.0.1:8000:8000 \
  -e JWT_SECRET=1d7a647e277b94094cbbc0ea01b3571c361a3d46313edd6a442ae317595159bf \
  -e API_KEYS=d1048800025cfbc2187d6a49a9c482f8cff91f63e70ac41a \
  -e POSTGRES_HOST=postgres \
  -e POSTGRES_PORT=5432 \
  -e POSTGRES_DB=plantos \
  -e POSTGRES_USER=plantos \
  -e POSTGRES_PASSWORD=plantos_test \
  -e TDENGINE_HOST=tdengine \
  -e TDENGINE_PORT=6041 \
  -e TDENGINE_DATABASE=plantos_ts \
  -e TDENGINE_USER=root \
  -e TDENGINE_PASSWORD=taosdata \
  -e EMQX_HOST=emqx \
  -e EMQX_MQTT_PORT=1883 \
  "plantos-backend:$RELEASE_SHORT"

echo "=== Step 7: Wait and verify ==="
sleep 8
echo "--- Backend logs ---"
docker logs plantos-backend --tail 10 2>&1
echo "--- Health ---"
curl -s http://localhost:8000/api/v1/health 2>&1 | head -c 200
echo ""
echo "--- Login ---"
curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"PlantOS@2026!"}' 2>&1 | head -c 100
echo ""
echo "--- Edge Nodes ---"
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login -H 'Content-Type: application/json' -d '{"username":"admin","password":"PlantOS@2026!"}' | python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token',''))")
curl -s "http://localhost:8000/api/v1/edge-nodes" -H "Authorization: Bearer $TOKEN" 2>&1 | head -c 200
echo ""
echo "--- Historian ---"
curl -s "http://localhost:8000/api/v1/measurements/history?signal_id=COMP-01.motor_current&from=2026-07-20T00:00&to=2026-07-23T23:59" -H "Authorization: Bearer $TOKEN" 2>&1 | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'DATA_COUNT={len(d.get(\"measurements\",d.get(\"data\",[])))}')" 2>&1
echo ""
echo "DONE"
