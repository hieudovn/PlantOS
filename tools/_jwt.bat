@echo off
echo y | pscp -pw PlantOS@2026! d:/Project/Github/PlantOS/tools/fix_edge_jwt.sh plantos@103.97.132.249:/tmp/fix_edge_jwt.sh
echo y | plink -ssh -pw PlantOS@2026! plantos@103.97.132.249 bash /tmp/fix_edge_jwt.sh
echo DONE
