#!/bin/bash
# Check CI status and trigger workflow dispatch on exact merge SHA
MERGE_SHA="d3e8ef763b33ed7357316d0d6d33d634ba6e7e98"

echo "=== CI Run #95 (fac6418) ==="
curl -s https://api.github.com/repos/hieudovn/PlantOS/actions/runs/30066814789 | python3 -c "
import sys,json
d=json.load(sys.stdin)
print('Status:', d.get('status'), d.get('conclusion'))
print('SHA:', d.get('head_sha','')[:12])
print('Branch:', d.get('head_branch'))
"

echo ""
echo "=== CI Run #94 (c9521d8) ==="
curl -s https://api.github.com/repos/hieudovn/PlantOS/actions/runs/30066600157 | python3 -c "
import sys,json
d=json.load(sys.stdin)
print('Status:', d.get('status'), d.get('conclusion'))
print('SHA:', d.get('head_sha','')[:12])
"

echo ""
echo "=== Triggering workflow_dispatch on $MERGE_SHA ==="
# Use GitHub API to trigger workflow dispatch
curl -s -X POST \
  "https://api.github.com/repos/hieudovn/PlantOS/actions/workflows/phase8-quality-gate.yml/dispatches" \
  -H "Accept: application/vnd.github.v3+json" \
  -H "Authorization: token ${GITHUB_TOKEN:-}" \
  -d "{\"ref\":\"$MERGE_SHA\"}" 2>&1 || echo "Need GITHUB_TOKEN env var"

echo ""
echo "=== Alternative: Push a lightweight tag at merge SHA ==="
echo "Run: git tag -a phase8-final-d3e8ef7 $MERGE_SHA -m 'Phase 8 final CI trigger'"
echo "Then: git push origin phase8-final-d3e8ef7"
echo "(Workflow may trigger on tag push depending on config)"
