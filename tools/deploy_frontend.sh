#!/bin/bash
set -e
SHA=801e952

echo "=== Build Frontend ==="
cd /opt/plantos
git checkout -f --detach $SHA 2>/dev/null || true

# Build frontend with correct API URL
cd frontend
echo "VITE_API_BASE_URL=" > .env.production
npm ci 2>&1 | tail -3
npm run build 2>&1 | tail -5

echo "=== Deploy Frontend ==="
docker stop plantos-frontend 2>/dev/null || true
docker rm plantos-frontend 2>/dev/null || true

# Copy dist to nginx serve path
sudo rm -rf /opt/plantos/frontend/dist/*
sudo cp -r dist/* /opt/plantos/frontend/dist/
sudo chmod -R 755 /opt/plantos/frontend/dist

echo "=== Restart nginx ==="
sudo nginx -t && sudo systemctl reload nginx

echo "=== Verify ==="
curl -sk -o /dev/null -w '%{http_code}' https://localhost/
echo " -> HTTPS frontend"
curl -sk -o /dev/null -w '%{http_code}' https://localhost/historian
echo " -> Historian page"

echo DONE
