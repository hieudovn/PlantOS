#!/bin/bash
echo "=== Tagging images with release SHA d3e8ef7 ==="
docker tag plantos-backend:801e952 plantos-backend:d3e8ef7
docker tag deployment-frontend:latest plantos-frontend:d3e8ef7
docker tag plantos-edge-v2:patched plantos-edge-v2:d3e8ef7

echo "Release images:"
docker images --format '{{.Repository}}:{{.Tag}}' | grep d3e8ef7

echo ""
echo "=== Image digests ==="
docker inspect plantos-backend:d3e8ef7 --format 'Backend: {{.Id}}'
docker inspect plantos-frontend:d3e8ef7 --format 'Frontend: {{.Id}}'
docker inspect plantos-edge-v2:d3e8ef7 --format 'Edge v2: {{.Id}}'
