@echo off
echo y | plink -ssh -pw PlantOS@2026! plantos@103.97.132.249 "cat /tmp/live_seeder.log 2>&1; echo ===BACKEND_INGEST===; docker logs plantos-backend --tail 5 2>&1 | grep -E 'ingest|20[01]'; echo ===TD===; docker exec plantos-tdengine taos -s 'use plantos_ts; show tables;' 2>&1 | grep -E 'comp01|pump101|filter101|tank101|motor_power|winding' | head -10; echo DONE"
