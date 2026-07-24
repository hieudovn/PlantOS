#!/bin/bash
# Phase 8 — Backup Restore Verification
set -e

TIMESTAMP=$(date -u +%Y-%m-%dT%H:%M:%SZ)
BACKUP_DIR=/tmp/phase8-backup-test
mkdir -p "$BACKUP_DIR"

echo "=== [1/5] Create PostgreSQL backup ==="
docker exec plantos-postgres pg_dump -U plantos -d plantos -Fc > "$BACKUP_DIR/plantos_backup.dump"
BACKUP_SIZE=$(stat -c%s "$BACKUP_DIR/plantos_backup.dump" 2>/dev/null || stat -f%z "$BACKUP_DIR/plantos_backup.dump")
echo "Backup size: $BACKUP_SIZE bytes"

echo "=== [2/5] Start isolated PG container ==="
docker rm -f plantos-pg-restore-test 2>/dev/null || true
docker run -d --name plantos-pg-restore-test \
  --network deployment_plantos-net \
  -e POSTGRES_USER=plantos \
  -e POSTGRES_PASSWORD=test123 \
  -e POSTGRES_DB=plantos \
  postgres:16-alpine

echo "Waiting for PG to start..."
for i in $(seq 1 15); do
  if docker exec plantos-pg-restore-test pg_isready -U plantos 2>/dev/null; then
    echo "PG ready!"
    break
  fi
  sleep 2
done

echo "=== [3/5] Restore backup ==="
docker cp "$BACKUP_DIR/plantos_backup.dump" plantos-pg-restore-test:/tmp/backup.dump
docker exec plantos-pg-restore-test pg_restore -U plantos -d plantos /tmp/backup.dump 2>&1 | tail -5
RESTORE_RC=${PIPESTATUS[0]}
PG_RESTORE_OK=false
if [ "$RESTORE_RC" = "0" ] || [ -z "$RESTORE_RC" ]; then
  PG_RESTORE_OK=true
fi

echo "=== [4/5] Verify integrity ==="
VERIFY_OK=true

# Check tables exist
TABLES=$(docker exec plantos-pg-restore-test psql -U plantos -d plantos -t -c "SELECT count(*) FROM information_schema.tables WHERE table_schema='public';" 2>/dev/null | tr -d ' ')
echo "Tables: $TABLES"

# Check plants
PLANTS=$(docker exec plantos-pg-restore-test psql -U plantos -d plantos -t -c "SELECT count(*) FROM plants;" 2>/dev/null | tr -d ' ')
echo "Plants: $PLANTS"

# Check assets
ASSETS=$(docker exec plantos-pg-restore-test psql -U plantos -d plantos -t -c "SELECT count(*) FROM assets;" 2>/dev/null | tr -d ' ')
echo "Assets: $ASSETS"

# Check signals
SIGNALS=$(docker exec plantos-pg-restore-test psql -U plantos -d plantos -t -c "SELECT count(*) FROM signals;" 2>/dev/null | tr -d ' ')
echo "Signals: $SIGNALS"

# Check users
USERS=$(docker exec plantos-pg-restore-test psql -U plantos -d plantos -t -c "SELECT count(*) FROM users;" 2>/dev/null | tr -d ' ')
echo "Users: $USERS"

# Check alembic version
ALEMBIC=$(docker exec plantos-pg-restore-test psql -U plantos -d plantos -t -c "SELECT version_num FROM alembic_version;" 2>/dev/null | tr -d ' ')
echo "Alembic: $ALEMBIC"

if [ "$TABLES" -gt 0 ] && [ "$PLANTS" -gt 0 ] && [ "$ASSETS" -gt 0 ] && [ "$USERS" -gt 0 ]; then
  VERIFY_OK=true
else
  VERIFY_OK=false
fi

echo "=== [5/5] TDengine check (no restore, verify data exists) ==="
TD_COUNT=$(docker exec plantos-tdengine taos -s "SELECT count(*) FROM plantos_ts.measurements;" 2>/dev/null | grep -oP '\d+' | head -1 || echo "0")
echo "TD measurements: $TD_COUNT"

# Cleanup
docker rm -f plantos-pg-restore-test 2>/dev/null || true

# Generate evidence
cat > /tmp/backup-restore-verification.json << EOF
{
  "collected_at": "$TIMESTAMP",
  "pg_backup_size_bytes": $BACKUP_SIZE,
  "pg_restore_ok": $PG_RESTORE_OK,
  "td_restore_ok": false,
  "td_restore_note": "TDengine backup/restore requires taosdump tool. Verified data exists ($TD_COUNT measurements).",
  "pg_integrity": {
    "tables": $TABLES,
    "plants": $PLANTS,
    "assets": $ASSETS,
    "signals": $SIGNALS,
    "users": $USERS,
    "alembic_version": "$ALEMBIC",
    "pass": $VERIFY_OK
  }
}
EOF

echo "Evidence saved to /tmp/backup-restore-verification.json"
cat /tmp/backup-restore-verification.json
echo ""
echo "DONE: PG_RESTORE_OK=$PG_RESTORE_OK VERIFY=$VERIFY_OK"
