@echo off
echo y | plink -ssh -pw PlantOS@2026! plantos@103.97.132.249 "docker logs plantos-edge-v2 2>&1 | grep -E 'JWT|login|heart|ingest|center|backend|authent|sync' | head -20; echo ---; docker logs plantos-edge-v2 2>&1 | tail -20; echo DONE"
