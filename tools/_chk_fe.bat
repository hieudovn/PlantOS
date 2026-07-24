@echo off
echo y | plink -ssh -pw PlantOS@2026! plantos@103.97.132.249 "cd /opt/plantos; git fetch origin phase8-closure 2>/dev/null; git checkout -f --detach 654f84d 2>/dev/null || true; head -3 frontend/Dockerfile; echo ---; grep 'FROM' frontend/Dockerfile; echo DONE"
