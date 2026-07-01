#!/bin/bash
# Master backup script — called by cron
set -euo pipefail

LOG="/var/log/plantos/backup.log"
mkdir -p "$(dirname "$LOG")" /backups/postgres /backups/tdengine

echo "=== Backup started: $(date) ===" >> "$LOG"

/opt/plantos/scripts/backup/pg-backup.sh >> "$LOG" 2>&1 || echo "PG BACKUP FAILED" >> "$LOG"
/opt/plantos/scripts/backup/tdengine-backup.sh >> "$LOG" 2>&1 || echo "TDENGINE BACKUP FAILED" >> "$LOG"

echo "=== Backup finished: $(date) ===" >> "$LOG"
