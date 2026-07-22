@echo off
echo === PORT 9998 ===
ssh -o StrictHostKeyChecking=no plantos@103.97.132.249 "ps aux | grep 1947066 | grep -v grep"
echo.
echo === PORT 9999 ===
ssh -o StrictHostKeyChecking=no plantos@103.97.132.249 "ps aux | grep 4012532 | grep -v grep"
echo.
echo === CHECK CREDENTIALS IN EDGE V2 ===
ssh -o StrictHostKeyChecking=no plantos@103.97.132.249 "docker exec plantos-edge-v2 env 2>/dev/null | grep -i secret\|pass\|key\|token || echo 'no env access'"
echo.
echo === NGINX TLS CHECK ===
ssh -o StrictHostKeyChecking=no plantos@103.97.132.249 "ls /etc/nginx/sites-enabled/ 2>/dev/null; cat /etc/nginx/nginx.conf 2>/dev/null | head -20"
