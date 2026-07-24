@echo off
echo y | plink -ssh -pw PlantOS@2026! plantos@103.97.132.249 "which node && node -v || echo NO_NODE; which npm && npm -v || echo NO_NPM; echo DONE"
