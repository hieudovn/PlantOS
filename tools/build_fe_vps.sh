#!/bin/bash
cd /opt/plantos
git fetch origin phase8-closure 2>/dev/null
git checkout -f --detach 654f84d 2>/dev/null || true

echo "=== Docker build frontend ==="
# Build using docker directly, not multi-stage target
docker build -f frontend/Dockerfile --target build -t plantos-fe-build frontend 2>&1

echo "=== Extract dist ==="
CID=$(docker create plantos-fe-build 2>/dev/null)
if [ -z "$CID" ]; then
  echo "No container created, trying alternative..."
  # Build as single stage
  docker build -t plantos-fe-build -f - frontend << 'DOCKERFILE'
FROM node:20-alpine
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm install
COPY . .
RUN npx vite build
DOCKERFILE
  CID=$(docker create plantos-fe-build)
fi

docker cp $CID:/app/dist /tmp/new-dist
docker rm $CID
ls /tmp/new-dist/
echo "BUILD_OK"

echo "=== Deploy ==="
rm -rf /opt/plantos/frontend/dist/*
cp -r /tmp/new-dist/* /opt/plantos/frontend/dist/
nginx -s reload 2>/dev/null || systemctl reload nginx 2>/dev/null

echo "=== Test ==="
curl -sk -o /dev/null -w '%{http_code}' https://localhost/
echo " -> index"
curl -sk -o /dev/null -w '%{http_code}' https://localhost/historian
echo " -> historian"
echo DONE
