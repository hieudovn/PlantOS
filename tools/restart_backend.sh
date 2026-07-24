#!/bin/bash
set -e
echo "=== Restarting backend with d3e8ef7 ==="
docker stop plantos-backend 2>/dev/null || true
docker rm plantos-backend 2>/dev/null || true
docker run -d --name plantos-backend \
  --network deployment_plantos-net \
  -p 127.0.0.1:8000:8000 \
  --env-file /opt/plantos/deployment/.env \
  --restart unless-stopped \
  plantos-backend:d3e8ef7

sleep 5
echo "Backend status:"
docker ps --filter name=plantos-backend --format '{{.Image}} {{.Status}}'
echo "Health check:"
curl -s http://localhost:8000/health
echo ""
echo "Backend DONE"
