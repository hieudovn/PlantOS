@echo off
echo ============================================================
echo PHASE 8 RUNTIME CONTAINMENT - EXECUTING
echo ============================================================

echo.
echo [1/7] KILLING EXPOSED TEST/SIMULATOR SERVERS...
ssh -o StrictHostKeyChecking=no plantos@103.97.132.249 "sudo kill 1947066 2>/dev/null; sudo kill 4012532 2>/dev/null; echo 'Killed ports 9998, 9999'"

echo.
echo [2/7] BACKUP CURRENT STATE...
ssh -o StrictHostKeyChecking=no plantos@103.97.132.249 "ss -tlnp > /tmp/ports-before-$(date +%%Y%%m%%d-%%H%%M%%S).txt 2>&1; docker ps > /tmp/docker-before.txt 2>&1; echo 'Backup done'"

echo.
echo [3/7] FIREWALL - RESTRICT INTERNAL PORTS...
ssh -o StrictHostKeyChecking=no plantos@103.97.132.249 "sudo ufw --force enable; sudo ufw allow 22/tcp; sudo ufw allow 80/tcp; sudo ufw allow 443/tcp; sudo ufw deny 4840/tcp; sudo ufw deny 4841/tcp; sudo ufw deny 7000/tcp; sudo ufw deny 8100/tcp; sudo ufw deny 8002/tcp; sudo ufw deny 8011/tcp; sudo ufw deny 9998/tcp; sudo ufw deny 9999/tcp; sudo ufw status verbose"

echo.
echo [4/7] VERIFY PORTS AFTER FIREWALL...
ssh -o StrictHostKeyChecking=no plantos@103.97.132.249 "ss -tlnp | grep '0.0.0.0'"

echo.
echo [5/7] DOCKER IMAGE DIGESTS...
ssh -o StrictHostKeyChecking=no plantos@103.97.132.249 "docker images --digests --format '{{.Repository}}:{{.Tag}} @{{.Digest}}' | grep plantos"

echo.
echo [6/7] CHECK REMAINING EXPOSED PORTS...
ssh -o StrictHostKeyChecking=no plantos@103.97.132.249 "ss -tlnp | grep '0.0.0.0' | awk '{print $4}' | sort -u"

echo.
echo [7/7] POSTGRES & TDENGINE BACKUP CHECK...
ssh -o StrictHostKeyChecking=no plantos@103.97.132.249 "ls -la /opt/plantos/backups/ 2>/dev/null || echo 'No backup dir'; docker exec plantos-postgres pg_dumpall -U plantos 2>&1 | head -5"

echo.
echo ============================================================
echo CONTAINMENT COMPLETE
echo ============================================================
