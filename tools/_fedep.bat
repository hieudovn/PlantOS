@echo off
echo y | pscp -pw PlantOS@2026! d:/Project/Github/PlantOS/tools/deploy_fe.sh plantos@103.97.132.249:/tmp/deploy_fe.sh
echo y | plink -ssh -pw PlantOS@2026! plantos@103.97.132.249 bash /tmp/deploy_fe.sh
echo DONE
