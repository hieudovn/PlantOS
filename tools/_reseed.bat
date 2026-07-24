@echo off
echo y | pscp -pw PlantOS@2026! d:/Project/Github/PlantOS/tools/restart_seeder.sh plantos@103.97.132.249:/tmp/restart_seeder.sh
echo y | plink -ssh -pw PlantOS@2026! plantos@103.97.132.249 bash /tmp/restart_seeder.sh
echo DONE
