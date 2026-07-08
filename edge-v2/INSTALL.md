# PlantOS Edge Lite v2 — Installation Guide

## Prerequisites

| Requirement | Minimum | Recommended |
|---|---|---|
| CPU | 1 core | 2 cores |
| RAM | 512 MB | 1 GB |
| Disk | 1 GB free | 10 GB (for time-series data) |
| OS | Ubuntu 22.04 / Debian 12 | Ubuntu 24.04 LTS |
| Python | 3.11 | 3.11+ |
| Docker | 24.0+ (optional) | 24.0+ |

## Option 1: Docker Compose (Recommended)

### 1. Prerequisites

```bash
sudo apt-get update
sudo apt-get install -y docker.io docker-compose-v2
sudo systemctl enable --now docker
```

### 2. Get the files

```bash
git clone --depth 1 --branch feature/edge-v2 https://github.com/PlantOS/plantos.git
cd plantos/edge-v2
```

### 3. Configure

```bash
cp agent/config/config.edge-v2.yaml agent/config/edge.yaml
# Edit agent/config/edge.yaml with your settings:
#   - Set center_url to your PlantOS Center URL
#   - Set api_key to your Center API key
#   - Change session_secret to a random value
```

### 4. Start

```bash
docker compose -f docker-compose.edge-v2.yml up -d
```

### 5. Verify

```bash
curl http://localhost:8011/api/status
# Expected: {"status": "running", "edge_node_id": "EDGEV2-PC-01", ...}

curl http://localhost:8011/api/version
# Expected: {"version": "2.0.0-dev", ...}

docker ps
# Expected: plantos-edge-v2 running, healthy
```

### 6. First-run setup

1. Open `http://localhost:8011` in a browser
2. Set admin password on the login page
3. Configure connectors via the Connections page
4. Verify heartbeat reaches Center at `/edge` in Center UI

### Docker Management

```bash
# View logs
docker logs plantos-edge-v2 -f

# Restart
docker restart plantos-edge-v2

# Stop
docker compose -f docker-compose.edge-v2.yml down

# Update (pull new image + restart)
docker compose -f docker-compose.edge-v2.yml pull
docker compose -f docker-compose.edge-v2.yml up -d

# Full cleanup (WARNING: removes data volume)
docker compose -f docker-compose.edge-v2.yml down -v
```

## Option 2: systemd (Native)

### 1. Run the installer

```bash
# From the edge-v2 directory:
sudo ./install.sh

# Or download and run:
curl -fsSL https://install.plantos.io/edge-v2 | sudo bash
```

### 2. Configure

```bash
sudo nano /etc/plantos-edge-v2/config.yaml
# Set: center_url, api_key, session_secret
```

### 3. Restart service

```bash
sudo systemctl restart plantos-edge-v2
```

### 4. Verify

```bash
sudo systemctl status plantos-edge-v2
# Expected: active (running)

curl http://localhost:8011/api/status
```

### systemd Management

```bash
# View logs
sudo journalctl -u plantos-edge-v2 -f

# Restart
sudo systemctl restart plantos-edge-v2

# Stop
sudo systemctl stop plantos-edge-v2

# Start on boot
sudo systemctl enable plantos-edge-v2

# Disable on boot
sudo systemctl disable plantos-edge-v2
```

## Post-Installation Checklist

- [ ] Admin password set via Console UI
- [ ] `center_url` points to running PlantOS Center
- [ ] Edge node visible in Center → `/edge` page
- [ ] Heartbeat shows as `online`
- [ ] Connectors configured (if connecting to PLCs/sensors)
- [ ] Data flowing into DuckDB buffer

## Troubleshooting

### Agent won't start

```bash
# Docker
docker logs plantos-edge-v2

# systemd
sudo journalctl -u plantos-edge-v2 -n 50 --no-pager
```

### Heartbeat not reaching Center

1. Check `center_url` in config
2. Verify Center API is reachable: `curl http://<center-url>/api/v1/edge-nodes`
3. Check network firewall (outbound to Center port)

### Config file not found

```bash
# Docker: verify volume mount
docker exec plantos-edge-v2 ls -la /app/config/

# systemd: verify path
sudo ls -la /etc/plantos-edge-v2/
```

### Port 8011 already in use

```bash
# Find the process
sudo lsof -i :8011

# Change port in config.yaml under web.port, restart
```
