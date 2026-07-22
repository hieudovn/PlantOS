@echo off
echo === PORT 7000 ===
ssh -o StrictHostKeyChecking=no plantos@103.97.132.249 "sudo lsof -i :7000 2>/dev/null || sudo ss -tlnp | grep :7000"
echo.
echo === PORT 8100 ===
ssh -o StrictHostKeyChecking=no plantos@103.97.132.249 "sudo lsof -i :8100 2>/dev/null || sudo ss -tlnp | grep :8100"
echo.
echo === PORT 9998 ===
ssh -o StrictHostKeyChecking=no plantos@103.97.132.249 "sudo lsof -i :9998 2>/dev/null || sudo ss -tlnp | grep :9998"
echo.
echo === PORT 9999 ===
ssh -o StrictHostKeyChecking=no plantos@103.97.132.249 "sudo lsof -i :9999 2>/dev/null || sudo ss -tlnp | grep :9999"
echo.
echo === PORT 4840 (OPC UA v1) ===
ssh -o StrictHostKeyChecking=no plantos@103.97.132.249 "ps aux | grep 3957396 | head -5"
echo.
echo === PORT 4841 + 8100 (OPC UA v2?) ===
ssh -o StrictHostKeyChecking=no plantos@103.97.132.249 "ps aux | grep 2745063 | head -5"
echo.
echo === PORT 8002 ===
ssh -o StrictHostKeyChecking=no plantos@103.97.132.249 "ps aux | grep virtual-factory | head -5"
echo.
echo === PORT 8011 (Edge v2) ===
ssh -o StrictHostKeyChecking=no plantos@103.97.132.249 "docker inspect plantos-edge-v2 --format '{{.Config.Env}}' 2>/dev/null | tr ',' '\n' | grep -i secret\|pass\|key\|token"
