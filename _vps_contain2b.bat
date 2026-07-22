@echo off
echo ============================================================
echo PHASE 8 CONTAINMENT - PHASE 2B
echo ============================================================

echo.
echo [1] CHECK DOCKER COMPOSE CONFIG...
ssh -o StrictHostKeyChecking=no plantos@103.97.132.249 "cat /opt/plantos/deployment/docker-compose.yml 2>/dev/null | head -80"

echo.
echo [2] GENERATE NEW SECRETS (simple)...
ssh -o StrictHostKeyChecking=no plantos@103.97.132.249 "openssl rand -hex 32 > /tmp/new_jwt_secret.txt && openssl rand -hex 32 > /tmp/new_session_secret.txt && openssl rand -hex 24 > /tmp/new_api_key.txt && openssl rand -base64 18 > /tmp/new_edge_password.txt && echo 'Generated 4 new secrets' && ls -la /tmp/new_*"

echo.
echo [3] BUILD IMMUTABLE EDGE V2 IMAGE FROM MAIN...
ssh -o StrictHostKeyChecking=no plantos@103.97.132.249 "cd /opt/plantos && git fetch origin main && git checkout main && git pull origin main && docker build --no-cache -t plantos-edge-v2:phase8-immutable -f edge-v2/Dockerfile . && docker images plantos-edge-v2:phase8-immutable --digests"

echo.
echo [4] BUILD IMMUTABLE BACKEND IMAGE...
ssh -o StrictHostKeyChecking=no plantos@103.97.132.249 "cd /opt/plantos && docker build --no-cache -t plantos-backend:phase8-immutable -f backend/Dockerfile . && docker images plantos-backend:phase8-immutable --digests"

echo.
echo [5] BUILD IMMUTABLE FRONTEND IMAGE...
ssh -o StrictHostKeyChecking=no plantos@103.97.132.249 "cd /opt/plantos && docker build --no-cache -t plantos-frontend:phase8-immutable -f frontend/Dockerfile . && docker images plantos-frontend:phase8-immutable --digests"

echo.
echo [6] VERIFY IMMUTABLE IMAGES...
ssh -o StrictHostKeyChecking=no plantos@103.97.132.249 "docker images --format '{{.Repository}}:{{.Tag}} | {{.ID}} | {{.Size}}' | grep phase8-immutable"

echo.
echo ============================================================
