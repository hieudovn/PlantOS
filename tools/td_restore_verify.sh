#!/bin/bash
# TDengine Backup & Restore Verification
set -e

echo "=== [1] Backup TDengine ==="
mkdir -p /tmp/td_backup
docker exec plantos-tdengine taosdump -o /tmp/td_backup plantos_ts 2>&1 | tail -5
echo "Backup files:"
ls -la /tmp/td_backup/
BACKUP_SIZE=$(du -sh /tmp/td_backup/ | cut -f1)
echo "Size: $BACKUP_SIZE"

echo ""
echo "=== [2] Start isolated TD container ==="
docker rm -f td-restore-test 2>/dev/null || true
docker run -d --name td-restore-test -p 6042:6030 \
  -e TAOS_FQDN=localhost \
  tdengine/tdengine:latest
echo "Waiting for TD..."
for i in $(seq 1 15); do
  if docker exec td-restore-test taos -s "SELECT 1" 2>/dev/null | grep -q '1'; then
    echo "TD ready!"
    break
  fi
  sleep 2
done

echo ""
echo "=== [3] Restore into test container ==="
docker cp /tmp/td_backup/. td-restore-test:/tmp/td_backup/
docker exec td-restore-test taosdump -i /tmp/td_backup 2>&1 | tail -10

echo ""
echo "=== [4] Verify integrity ==="
COUNT=$(docker exec td-restore-test taos -s "SELECT count(*) FROM plantos_ts.measurements;" 2>/dev/null | grep -oP '\d+' | head -1)
echo "Measurements restored: $COUNT"

TABLES=$(docker exec td-restore-test taos -s "SELECT count(*) FROM information_schema.ins_tables WHERE db_name='plantos_ts';" 2>/dev/null | grep -oP '\d+' | head -1)
echo "Tables: $TABLES"

if [ -n "$COUNT" ] && [ "$COUNT" -gt 0 ]; then
  TD_RESTORE_OK=true
else
  TD_RESTORE_OK=false
fi

echo ""
echo "=== [5] Cleanup ==="
docker rm -f td-restore-test

# Generate evidence
cat > /tmp/td-restore-result.json << EOF
{
  "collected_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "td_backup_size": "$BACKUP_SIZE",
  "td_restore_ok": $TD_RESTORE_OK,
  "td_restored_count": "$COUNT",
  "td_tables": "$TABLES"
}
EOF

echo ""
echo "=== Result ==="
cat /tmp/td-restore-result.json
echo "TD_RESTORE_OK=$TD_RESTORE_OK"
