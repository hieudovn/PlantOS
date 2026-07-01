# Phase 6 — Task 6-03: Database Backup (PostgreSQL + TDengine)

> **Designer:** V4 Pro | **Date:** 2026-07-01 | **Priority:** P0

## Context

PlantOS hiện có ~200K+ measurements trong TDengine và toàn bộ asset/signal metadata trong PostgreSQL. **Chưa có backup nào.** Nếu VPS crash hoặc disk fail, toàn bộ dữ liệu mất. Cần backup tự động hàng ngày.

## Current State

```
PostgreSQL (Docker: plantos-postgres)
├─ Database: plantos
├─ Tables: assets, signals, areas, plants, edge_nodes, alarms, users
└─ Size: ~5-10 MB (metadata only, nhẹ)

TDengine (Docker: plantos-tdengine)
├─ Database: plantos_ts
├─ Supertable: measurements
├─ Child tables: ~26 (d_COMP01-CORE_speed, ...)
└─ Size: ~50-100 MB (đang tăng ~1-2MB/ngày với OPC UA 26 signals)
```

## Target Architecture

```
┌──────────────────────────────────────────────────────┐
│                   Cron (daily @ 2AM)                  │
│                                                       │
│  pg-backup.sh                    tdengine-backup.sh   │
│  ├─ docker exec pg_dump          ├─ taosdump          │
│  ├─ gzip                          ├─ gzip             │
│  └─ /backups/postgres/            └─ /backups/tdengine/│
│                                                       │
│  Retention: 7 ngày local + optional S3 sync           │
└──────────────────────────────────────────────────────┘
```

## Implementation Checklist

- [ ] CREATE `scripts/backup/pg-backup.sh` — PostgreSQL dump script
- [ ] CREATE `scripts/backup/tdengine-backup.sh` — TDengine backup script  
- [ ] CREATE `scripts/backup/backup-all.sh` — master backup script
- [ ] SETUP cron job on VPS: `0 2 * * * /opt/plantos/scripts/backup/backup-all.sh`
- [ ] CREATE `deployment/backup/` folder with backup config
- [ ] VERIFY: manual run creates backup files
- [ ] VERIFY: backup files are valid (pg_restore dry-run, taosdump check)
- [ ] UPDATE `docs/19-deployment-design.md` — add backup section

## Detailed Instructions

### 1. pg-backup.sh

File: `scripts/backup/pg-backup.sh`

```bash
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
```

### 2. tdengine-backup.sh

File: `scripts/backup/tdengine-backup.sh`

```bash
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
```

### 3. backup-all.sh

File: `scripts/backup/backup-all.sh`

```bash
#!/bin/bash
# Master backup script — called by cron
set -euo pipefail

LOG="/var/log/plantos/backup.log"
mkdir -p "$(dirname "$LOG")" /backups/postgres /backups/tdengine

echo "=== Backup started: $(date) ===" >> "$LOG"

/opt/plantos/scripts/backup/pg-backup.sh >> "$LOG" 2>&1 || echo "PG BACKUP FAILED" >> "$LOG"
/opt/plantos/scripts/backup/tdengine-backup.sh >> "$LOG" 2>&1 || echo "TDENGINE BACKUP FAILED" >> "$LOG"

echo "=== Backup finished: $(date) ===" >> "$LOG"
```

### 4. Cron Setup

On VPS (`crontab -e` for plantos user):

```cron
# PlantOS daily backup at 2:00 AM ICT (UTC+7 = 19:00 UTC)
0 2 * * * /opt/plantos/scripts/backup/backup-all.sh
```

### 5. Validation

| Check | Command | Expected |
|---|---|---|
| Manual PG backup | `bash scripts/backup/pg-backup.sh` | Creates `.dump` file in `/backups/postgres/` |
| Verify PG backup | `docker exec -i plantos-postgres pg_restore -l /backups/postgres/plantos_*.dump \| head` | Lists database objects |
| Manual TD backup | `bash scripts/backup/tdengine-backup.sh` | Creates `.tar.gz` in `/backups/tdengine/` |
| Cron is active | `crontab -l \| grep backup` | Shows the backup line |
| Retention works | Check after 8 days | Files older than 7 days deleted |

## Notes

- Backup directory `/backups/` nên mount volume riêng nếu có disk riêng cho backup
- TDengine `taosdump` có thể không hỗ trợ trên ARM — nếu fail, fallback sang `SELECT *` CSV export
- Cân nhắc thêm S3 sync trong Phase 7 (rclone hoặc aws s3 sync)
- **Restore test** sẽ là task riêng trong Phase 7
