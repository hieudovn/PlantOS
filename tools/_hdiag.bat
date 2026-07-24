@echo off
echo y | pscp -pw PlantOS@2026! d:/Project/Github/PlantOS/tools/hist_diag.sh plantos@103.97.132.249:/tmp/hist_diag.sh
echo y | plink -ssh -pw PlantOS@2026! plantos@103.97.132.249 bash /tmp/hist_diag.sh
echo DONE
