@echo off
echo y | plink -ssh -pw PlantOS@2026! plantos@103.97.132.249 "echo ===DNS_TEST===; docker exec plantos-edge-v2 nslookup backend 2>&1 || docker exec plantos-edge-v2 getent hosts backend 2>&1 || docker exec plantos-edge-v2 ping -c1 backend 2>&1 | head -3; echo ===CENTER_URL===; grep center_url /opt/plantos/edge-v2/agent/config/config.edge-v2.yaml | head -3; echo DONE"
