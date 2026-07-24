@echo off
echo y | pscp -pw PlantOS@2026! d:/Project/Github/PlantOS/tools/vfy_data.sh plantos@103.97.132.249:/tmp/vfy_data.sh
echo y | plink -ssh -pw PlantOS@2026! plantos@103.97.132.249 bash /tmp/vfy_data.sh
echo DONE
