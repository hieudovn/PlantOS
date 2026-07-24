#!/bin/bash
cd /opt/plantos
git fetch origin phase8-closure 2>/dev/null
git checkout -f --detach f3263e0 2>/dev/null || true
docker build -f frontend/Dockerfile --target build -t plantos-fe-build frontend 2>&1 | tail -3
CID=$(docker create plantos-fe-build)
docker cp $CID:/app/dist /tmp/new-dist
docker rm $CID
rm -rf /opt/plantos/frontend/dist/*
cp -r /tmp/new-dist/* /opt/plantos/frontend/dist/
nginx -s reload 2>/dev/null || systemctl reload nginx 2>/dev/null
echo "DEPLOYED"
curl -sk -o /dev/null -w '%{http_code}' https://localhost/historian
echo ""
echo DONE
