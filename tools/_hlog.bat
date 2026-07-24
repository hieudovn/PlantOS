@echo off
echo y | plink -ssh -pw PlantOS@2026! plantos@103.97.132.249 "docker logs plantos-backend --tail 20 2>&1 | grep -E 'TDengine|historian|stub|connect|error|Error' | head -15; echo DONE"
