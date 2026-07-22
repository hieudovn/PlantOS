@echo off
echo === DOCKER ===
ssh -o StrictHostKeyChecking=no plantos@103.97.132.249 "docker ps --format 'table {{.Names}}\t{{.Image}}\t{{.Ports}}'"
echo.
echo === PORTS ===
ssh -o StrictHostKeyChecking=no plantos@103.97.132.249 "ss -tlnp 2>/dev/null || netstat -tlnp 2>/dev/null"
echo.
echo === IMAGES ===
ssh -o StrictHostKeyChecking=no plantos@103.97.132.249 "docker images --format '{{.Repository}}:{{.Tag}} | {{.ID}}'"
