@echo off
echo y | pscp -pw PlantOS@2026! d:/Project/Github/PlantOS/tools/revert_seed.sh plantos@103.97.132.249:/tmp/revert_seed.sh
echo y | plink -ssh -pw PlantOS@2026! plantos@103.97.132.249 bash /tmp/revert_seed.sh
echo DONE
