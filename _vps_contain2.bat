@echo off
echo ============================================================
echo PHASE 8 RUNTIME CONTAINMENT - PHASE 2
echo ============================================================

echo.
echo [1/6] CHECK CURRENT CREDENTIALS...
ssh -o StrictHostKeyChecking=no plantos@103.97.132.249 "echo '--- Edge v2 env ---' && docker inspect plantos-edge-v2 --format '{{range .Config.Env}}{{println .}}{{end}}' 2>/dev/null | grep -i secret\|pass\|key\|token || echo 'no env'"
echo.
echo "--- Backend env ---"
ssh -o StrictHostKeyChecking=no plantos@103.97.132.249 "docker inspect plantos-backend --format '{{range .Config.Env}}{{println .}}{{end}}' 2>/dev/null | grep -i secret\|key\|token\|pass || echo 'no env'"

echo.
echo [2/6] GENERATE NEW SECRETS...
ssh -o StrictHostKeyChecking=no plantos@103.97.132.249 "echo 'NEW_JWT_SECRET='\$(openssl rand -hex 32); echo 'NEW_SESSION_SECRET='\$(openssl rand -hex 32); echo 'NEW_API_KEY='\$(openssl rand -hex 24); echo 'NEW_EDGE_PASSWORD='\$(openssl rand -base64 18)"

echo.
echo [3/6] CHECK DOCKER COMPOSE ENV FILE...
ssh -o StrictHostKeyChecking=no plantos@103.97.132.249 "cat /opt/plantos/deployment/.env 2>/dev/null | grep -i secret\|key\|token\|pass || echo 'no .env file'"

echo.
echo [4/6] BUILD IMMUTABLE IMAGE FROM CURRENT COMMIT...
ssh -o StrictHostKeyChecking=no plantos@103.97.132.249 "cd /opt/plantos && git log --oneline -3"

echo.
echo [5/6] CURRENT IMAGE DIGESTS FOR MANIFEST...
ssh -o StrictHostKeyChecking=no plantos@103.97.132.249 "docker images --digests --format '{{.Repository}}:{{.Tag}} sha256:{{.Digest}}' 2>/dev/null | grep plantos"

echo.
echo [6/6] CHECK TLS CERT...
ssh -o StrictHostKeyChecking=no plantos@103.97.132.249 "ls /etc/letsencrypt/live/ 2>/dev/null || echo 'No Let'\''s Encrypt certs'; ls /etc/nginx/ssl/ 2>/dev/null || echo 'No SSL dir'"

echo.
echo ============================================================
