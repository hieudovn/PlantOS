#!/bin/bash
# TDengine backup — runs via cron daily
set -euo pipefail

BACKUP_DIR="/backups/tdengine"
RETENTION_DAYS=7
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
CONTAINER="plantos-tdengine"
DB_NAME="plantos_ts"
TEMP_DIR=$(mktemp -d)

mkdir -p "$BACKUP_DIR"

# Use taosdump inside container, output to temp dir
docker exec "$CONTAINER" taosdump -D "$DB_NAME" -o /tmp/tdump 2>/dev/null || true

# Copy out and tar.gz
docker cp "$CONTAINER":/tmp/tdump/. "$TEMP_DIR/" 2>/dev/null || true
tar -czf "$BACKUP_DIR/tdengine_${TIMESTAMP}.tar.gz" -C "$TEMP_DIR" .

# Cleanup
rm -rf "$TEMP_DIR"
docker exec "$CONTAINER" rm -rf /tmp/tdump 2>/dev/null || true
find "$BACKUP_DIR" -name "tdengine_*.tar.gz" -mtime +$RETENTION_DAYS -delete

echo "[$(date)] TDengine backup OK: tdengine_${TIMESTAMP}.tar.gz ($(du -h "$BACKUP_DIR/tdengine_${TIMESTAMP}.tar.gz" | cut -f1))"
