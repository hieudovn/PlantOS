#!/bin/bash
set -e
SHA=654f84d

echo "=== Build Frontend ==="
cd /opt/plantos
git checkout -f --detach $SHA 2>/dev/null || true

# Build dist using Docker multi-stage
docker build --target build -t plantos-frontend-build:$SHA -f frontend/Dockerfile frontend 2>&1 | tail -5
CID=$(docker create plantos-frontend-build:$SHA)
docker cp $CID:/app/dist /tmp/frontend-dist
docker rm $CID
echo "DIST_EXTRACTED: $(ls /tmp/frontend-dist | head -3)"

echo "=== Deploy ==="
rm -rf /opt/plantos/frontend/dist/*
cp -r /tmp/frontend-dist/* /opt/plantos/frontend/dist/
sudo nginx -t 2>/dev/null && sudo systemctl reload nginx 2>/dev/null || { nginx -t && systemctl reload nginx; }
echo "DEPLOYED"

echo "=== Verify ==="
curl -sk -o /dev/null -w '%{http_code}' https://localhost/
echo " -> index"
curl -sk -o /dev/null -w '%{http_code}' https://localhost/historian
echo " -> historian"

echo DONE
