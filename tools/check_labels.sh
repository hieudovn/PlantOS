#!/bin/bash
echo "=== Checking OCI labels ==="

for img in plantos-backend:d3e8ef7 plantos-frontend:d3e8ef7 plantos-edge-v2:d3e8ef7; do
  echo ""
  echo "--- $img ---"
  REV=$(docker image inspect "$img" --format '{{index .Config.Labels "org.opencontainers.image.revision"}}' 2>/dev/null)
  VER=$(docker image inspect "$img" --format '{{index .Config.Labels "org.opencontainers.image.version"}}' 2>/dev/null)
  CREATED=$(docker image inspect "$img" --format '{{index .Config.Labels "org.opencontainers.image.created"}}' 2>/dev/null)
  IMG_ID=$(docker image inspect "$img" --format '{{.Id}}' 2>/dev/null)
  
  if [ -n "$REV" ]; then
    echo "  revision: $REV"
    echo "  version:  $VER"
    echo "  created:  $CREATED"
    echo "  image_id: $IMG_ID"
    if [[ "$REV" == d3e8ef7* ]]; then
      echo "  STATUS: PASS (revision matches merge SHA)"
    else
      echo "  STATUS: FAIL (revision mismatch)"
    fi
  else
    echo "  STATUS: FAIL (no OCI revision label)"
  fi
done
