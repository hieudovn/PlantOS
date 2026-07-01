#!/bin/bash
# PostgreSQL backup — runs via cron daily
set -euo pipefail

BACKUP_DIR="/backups/postgres"
RETENTION_DAYS=7
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
CONTAINER="plantos-postgres"
DB_NAME="plantos"
DB_USER="plantos"

mkdir -p "$BACKUP_DIR"

# Dump
docker exec "$CONTAINER" pg_dump -U "$DB_USER" -d "$DB_NAME" \
  --format=custom --compress=9 \
  > "$BACKUP_DIR/${DB_NAME}_${TIMESTAMP}.dump"

# Keep only last N days
find "$BACKUP_DIR" -name "*.dump" -mtime +$RETENTION_DAYS -delete

echo "[$(date)] PG backup OK: ${DB_NAME}_${TIMESTAMP}.dump ($(du -h "$BACKUP_DIR/${DB_NAME}_${TIMESTAMP}.dump" | cut -f1))"
