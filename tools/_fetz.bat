@echo off
echo y | pscp -pw PlantOS@2026! d:/Project/Github/PlantOS/tools/fe_tz_deploy.sh plantos@103.97.132.249:/tmp/fe_tz_deploy.sh
echo y | plink -ssh -pw PlantOS@2026! plantos@103.97.132.249 bash /tmp/fe_tz_deploy.sh
echo DONE
