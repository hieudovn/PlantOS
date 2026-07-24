@echo off
echo y | pscp -pw PlantOS@2026! d:/Project/Github/PlantOS/tools/seed_debug.sh plantos@103.97.132.249:/tmp/seed_debug.sh
echo y | plink -ssh -pw PlantOS@2026! plantos@103.97.132.249 bash /tmp/seed_debug.sh
echo DONE
