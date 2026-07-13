#!/bin/bash
# Create stub files for missing modules
cd /opt/plantos/frontend/src/features/operations

mkdir -p components
echo 'export const config = {};' > config.ts
echo 'export const ConditionScoreCard = () => null;' > components/ConditionScoreCard.tsx
echo 'export const KeySignalsCard = () => null;' > components/KeySignalsCard.tsx
echo 'export const AlarmTimeline = () => null;' > components/AlarmTimeline.tsx

# Create the config file that useProcessConfig imports
echo 'export function getPlantConfig(plantId: string) { return {}; }' > ../config.ts 2>/dev/null || true

# Also fix the hooks config import
cd /opt/plantos/frontend/src/features/operations/hooks
echo 'export const config = {};' > ../config.ts 2>/dev/null || true

echo "Stubs created"
