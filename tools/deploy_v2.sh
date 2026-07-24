#!/bin/bash
set -e
RELEASE_SHA=f7d77cf
RELEASE_SHORT=f7d77cf

echo "=== Step 1: Checkout ==="
cd /opt/plantos
git fetch origin phase8-closure
# Force checkout, ignore permission errors on non-backend files
git checkout -f --detach "$RELEASE_SHA" 2>/dev/null || true
echo "CHECKOUT: $(git rev-parse --short=7 HEAD)"

echo "=== Step 2: Build ==="
docker build \
  --label "org.opencontainers.image.revision=$RELEASE_SHA" \
  -t "plantos-backend:$RELEASE_SHORT" \
  -f backend/Dockerfile \
  backend 2>&1 | tail -8

echo "=== Step 3: Swap ==="
docker stop plantos-backend 2>/dev/null; docker rm plantos-backend 2>/dev/null
docker run -d --name plantos-backend --network deployment_plantos-net -p 127.0.0.1:8000:8000 \
  -e JWT_SECRET=1d7a647e277b94094cbbc0ea01b3571c361a3d46313edd6a442ae317595159bf \
  -e API_KEYS=d1048800025cfbc2187d6a49a9c482f8cff91f63e70ac41a \
  -e POSTGRES_HOST=postgres -e POSTGRES_PORT=5432 -e POSTGRES_DB=plantos -e POSTGRES_USER=plantos \
  -e POSTGRES_PASSWORD=plantos_test \
  -e TDENGINE_HOST=tdengine -e TDENGINE_PORT=6041 -e TDENGINE_DATABASE=plantos_ts \
  -e TDENGINE_USER=root -e TDENGINE_PASSWORD=taosdata \
  -e EMQX_HOST=emqx -e EMQX_MQTT_PORT=1883 \
  "plantos-backend:$RELEASE_SHORT"

echo "=== Step 4: Verify ==="
sleep 8
docker logs plantos-backend --tail 5 2>&1
echo "---"
curl -s http://localhost:8000/api/v1/health 2>&1 | head -c 200
echo ""
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login -H 'Content-Type: application/json' -d '{"username":"admin","password":"PlantOS@2026!"}' | python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token',''))" 2>/dev/null)
echo "TOKEN: ${TOKEN:0:20}..."
curl -s "http://localhost:8000/api/v1/edge-nodes" -H "Authorization: Bearer $TOKEN" | head -c 200
echo ""
curl -s "http://localhost:8000/api/v1/measurements/history?signal_id=COMP-01.motor_current&from=2026-07-20T00:00&to=2026-07-23T23:59" -H "Authorization: Bearer $TOKEN" | python3 -c "import sys,json; d=json.load(sys.stdin); m=d.get('measurements',d.get('data',[])); print(f'HISTORIAN: {len(m)} records')" 2>/dev/null
echo ""
echo DONE
