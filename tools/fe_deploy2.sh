#!/bin/bash
cd /opt/plantos
git checkout -f --detach 654f84d 2>/dev/null || true

echo "=== Build Frontend ==="
docker build --target build -t plantos-fe-build:654f84d -f frontend/Dockerfile frontend 2>&1 | tail -8

echo "=== Extract ==="
CID=$(docker create plantos-fe-build:654f84d 2>/dev/null)
docker cp $CID:/app/dist /tmp/frontend-dist 2>&1
docker rm $CID 2>/dev/null

echo "DIST: $(ls /tmp/frontend-dist 2>/dev/null | head -3)"

echo "=== Deploy ==="
rm -rf /opt/plantos/frontend/dist/*
cp -r /tmp/frontend-dist/* /opt/plantos/frontend/dist/ 2>/dev/null
systemctl reload nginx 2>/dev/null || nginx -s reload 2>/dev/null
echo "DEPLOYED"

echo "=== Test ==="
curl -sk -o /dev/null -w '%{http_code}' https://localhost/historian
echo ""
echo DONE
