@echo off
echo y | pscp -pw PlantOS@2026! d:/Project/Github/PlantOS/tools/tz_test.sh plantos@103.97.132.249:/tmp/tz_test.sh
echo y | plink -ssh -pw PlantOS@2026! plantos@103.97.132.249 bash /tmp/tz_test.sh
echo DONE
