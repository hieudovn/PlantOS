@echo off
echo y | pscp -pw PlantOS@2026! d:/Project/Github/PlantOS/tools/ts_check.sh plantos@103.97.132.249:/tmp/ts_check.sh
echo y | plink -ssh -pw PlantOS@2026! plantos@103.97.132.249 bash /tmp/ts_check.sh
echo DONE
