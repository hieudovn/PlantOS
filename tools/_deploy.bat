@echo off
echo y | pscp -pw PlantOS@2026! d:/Project/Github/PlantOS/tools/deploy_phase8.sh plantos@103.97.132.249:/tmp/deploy_phase8.sh
echo y | plink -ssh -pw PlantOS@2026! plantos@103.97.132.249 bash /tmp/deploy_phase8.sh
echo DONE
