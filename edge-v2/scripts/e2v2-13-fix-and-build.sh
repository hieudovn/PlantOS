#!/bin/bash
cd /opt/plantos/frontend/src/features/operations
mkdir -p components
echo 'export const config = {};' > config.ts
echo 'export const ConditionScoreCard = () => null;' > components/ConditionScoreCard.tsx
echo 'export const KeySignalsCard = () => null;' > components/KeySignalsCard.tsx
echo 'export const AlarmTimeline = () => null;' > components/AlarmTimeline.tsx
cd /opt/plantos/frontend
npx vite build 2>&1 | tail -15
