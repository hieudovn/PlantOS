#!/bin/bash
cd /opt/plantos
git fetch origin phase8-closure 2>/dev/null
git checkout -f --detach 9b914b5 2>/dev/null || true

echo "=== Build ==="
docker build -f frontend/Dockerfile --target build -t plantos-fe-build frontend 2>&1 | tail -5

echo "=== Extract ==="
CID=$(docker create plantos-fe-build)
docker cp $CID:/app/dist /tmp/new-dist2
docker rm $CID

echo "=== Deploy ==="
rm -rf /opt/plantos/frontend/dist/*
cp -r /tmp/new-dist2/* /opt/plantos/frontend/dist/
nginx -s reload 2>/dev/null || systemctl reload nginx 2>/dev/null

echo "=== Test ==="
curl -sk -o /dev/null -w '%{http_code}' https://localhost/historian
echo ""
echo DONE
