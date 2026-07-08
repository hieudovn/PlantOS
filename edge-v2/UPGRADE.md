# PlantOS Edge Lite v2 — Upgrade Guide

## Backup First

Always backup config and data before upgrading:

```bash
# Backup config (Edge v2 API)
curl -X POST http://localhost:8011/api/config/backup

# Or manually:
cp /etc/plantos-edge-v2/config.yaml /etc/plantos-edge-v2/config.yaml.bak
```

## Docker Upgrade

```bash
cd /opt/plantos-edge-v2

# 1. Pull latest code
git pull origin feature/edge-v2

# 2. Rebuild and restart
docker compose -f docker-compose.edge-v2.yml build --no-cache
docker compose -f docker-compose.edge-v2.yml up -d

# 3. Verify
curl http://localhost:8011/api/version
```

## systemd Upgrade

```bash
cd /opt/plantos-edge-v2

# 1. Stop service
sudo systemctl stop plantos-edge-v2

# 2. Backup current venv (optional)
sudo mv venv venv.bak

# 3. Pull latest code
sudo git pull origin feature/edge-v2

# 4. Rebuild venv
sudo python3 -m venv venv
sudo venv/bin/pip install -r requirements.txt

# 5. Update systemd service if needed
sudo cp plantos-edge-v2.service /etc/systemd/system/
sudo systemctl daemon-reload

# 6. Start service
sudo systemctl start plantos-edge-v2

# 7. Verify
curl http://localhost:8011/api/version
sudo systemctl status plantos-edge-v2

# 8. Clean up old venv
sudo rm -rf venv.bak
```

## Verify After Upgrade

1. **Version**: `curl http://localhost:8011/api/version`
2. **Status**: `curl http://localhost:8011/api/status`
3. **Config**: `curl http://localhost:8011/api/config`
4. **Heartbeat**: Check Center → Edge Fleet → node is online
5. **Data**: Check signals are flowing on dashboard
6. **Connectors**: Verify all connectors are running

## Rollback

If the upgrade fails:

### Docker

```bash
# Revert to previous Docker image
docker compose -f docker-compose.edge-v2.yml down
git checkout HEAD~1  # Go back one commit
docker compose -f docker-compose.edge-v2.yml up -d --build
```

### systemd

```bash
sudo systemctl stop plantos-edge-v2
sudo git checkout HEAD~1
sudo python3 -m venv venv
sudo venv/bin/pip install -r requirements.txt
sudo systemctl start plantos-edge-v2
```

## Data Migration

The DuckDB database is backward-compatible within the same major version.
Downgrading may require restoring from a backup:

```bash
curl -X POST http://localhost:8011/api/config/restore \
  -H "Content-Type: application/json" \
  -d '{"path": "/opt/plantos-edge-v2/config/backups/config_backup_20260708_120000.yaml"}'
```
