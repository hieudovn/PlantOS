@echo off
echo y | pscp -pw PlantOS@2026! d:/Project/Github/PlantOS/tools/build_fe_vps.sh plantos@103.97.132.249:/tmp/build_fe_vps.sh
echo y | plink -ssh -pw PlantOS@2026! plantos@103.97.132.249 bash /tmp/build_fe_vps.sh
echo DONE
