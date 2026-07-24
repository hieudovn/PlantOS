@echo off
echo y | pscp -pw PlantOS@2026! d:/Project/Github/PlantOS/tools/td_check.sh plantos@103.97.132.249:/tmp/td_check.sh
echo y | plink -ssh -pw PlantOS@2026! plantos@103.97.132.249 bash /tmp/td_check.sh
echo DONE
