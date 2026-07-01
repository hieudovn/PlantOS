# Phase 6 — Task 6-02: Systemd Services (Edge Agent + Virtual Factory)

> **Designer:** V4 Pro | **Date:** 2026-07-01 | **Priority:** P0

## Context

Edge Agent và Virtual Factory hiện chạy bằng `nohup` / `setsid` thủ công trên VPS. Khi SSH session kết thúc hoặc process crash, không có auto-restart. Cần systemd services để đảm bảo **auto-start on boot** và **auto-restart on crash**.

## Current State

```bash
# Edge Agent - chạy thủ công
cd /opt/plantos/edge/agent && nohup python3 -u main.py > /tmp/edge.log 2>&1 &

# Virtual Factory - chạy thủ công
/usr/bin/python3.11 /home/plantos/.local/bin/virtual-factory serve \
  --config /opt/virtual-factory/configs/plants/compressor_train_benchmark_01.yaml \
  --host 0.0.0.0 --port 8002 --auto-start --opcua-endpoint opc.tcp://0.0.0.0:4840
```

## Target Architecture

```
┌─────────────────────────────────────────────┐
│              systemd (init)                  │
│                                              │
│  plantos-edge.service                       │
│  ├─ After=network.target docker.service      │
│  ├─ User=plantos                            │
│  ├─ WorkingDirectory=/opt/plantos/edge/agent │
│  ├─ ExecStart=python3 -u main.py            │
│  ├─ Restart=always                          │
│  └─ RestartSec=10                           │
│                                              │
│  plantos-vf.service                         │
│  ├─ After=network.target                    │
│  ├─ User=plantos                            │
│  ├─ ExecStart=virtual-factory serve ...     │
│  ├─ Restart=always                          │
│  └─ RestartSec=10                           │
└─────────────────────────────────────────────┘
```

## Implementation Checklist

- [ ] CREATE `/etc/systemd/system/plantos-edge.service`
- [ ] CREATE `/etc/systemd/system/plantos-vf.service`
- [ ] CREATE `deployment/systemd/` folder in repo with service templates
- [ ] VERIFY: `sudo systemctl enable plantos-edge plantos-vf`
- [ ] VERIFY: `sudo systemctl start plantos-edge plantos-vf`
- [ ] VERIFY: reboot test (services auto-start)
- [ ] UPDATE `docs/19-deployment-design.md` — add systemd section

## Detailed Instructions

### 1. plantos-edge.service

File: `deployment/systemd/plantos-edge.service`

```ini
[Unit]
Description=PlantOS Edge Agent
After=network.target docker.service
Wants=docker.service

[Service]
Type=simple
User=plantos
Group=plantos
WorkingDirectory=/opt/plantos/edge/agent
Environment=PYTHONUNBUFFERED=1
ExecStart=/usr/bin/python3 -u main.py
Restart=always
RestartSec=10
StandardOutput=append:/var/log/plantos/edge.log
StandardError=append:/var/log/plantos/edge.log

# Graceful shutdown
KillSignal=SIGTERM
TimeoutStopSec=15

[Install]
WantedBy=multi-user.target
```

### 2. plantos-vf.service

File: `deployment/systemd/plantos-vf.service`

```ini
[Unit]
Description=PlantOS Virtual Factory (OPC UA Simulator)
After=network.target
Wants=network.target

[Service]
Type=simple
User=plantos
Group=plantos
Environment=PATH=/home/plantos/.local/bin:/usr/bin:/usr/local/bin
ExecStart=/home/plantos/.local/bin/virtual-factory serve \
  --config /opt/virtual-factory/configs/plants/compressor_train_benchmark_01.yaml \
  --host 0.0.0.0 \
  --port 8002 \
  --auto-start \
  --opcua-endpoint opc.tcp://0.0.0.0:4840
Restart=always
RestartSec=10
StandardOutput=append:/var/log/plantos/vf.log
StandardError=append:/var/log/plantos/vf.log

KillSignal=SIGTERM
TimeoutStopSec=15

[Install]
WantedBy=multi-user.target
```

### 3. Deploy Steps

On VPS (run as root/plantos):

```bash
# Create log directory
sudo mkdir -p /var/log/plantos
sudo chown plantos:plantos /var/log/plantos

# Stop existing manual processes
sudo pkill -f "main.py" || true
sudo pkill -f "virtual-factory" || true

# Copy service files
sudo cp deployment/systemd/plantos-edge.service /etc/systemd/system/
sudo cp deployment/systemd/plantos-vf.service /etc/systemd/system/

# Reload & enable
sudo systemctl daemon-reload
sudo systemctl enable plantos-edge plantos-vf
sudo systemctl start plantos-edge plantos-vf

# Verify
sleep 10
systemctl status plantos-edge --no-pager
systemctl status plantos-vf --no-pager
curl -s http://localhost:8001/api/status
curl -s http://localhost:8002/health
```

### 4. Validation

| Check | Expected |
|---|---|
| `systemctl is-active plantos-edge` | `active` |
| `systemctl is-active plantos-vf` | `active` |
| `systemctl is-enabled plantos-edge` | `enabled` |
| Edge status API | 200 OK, uptime > 0 |
| VF health API | 200 OK |
| After manual `sudo systemctl stop plantos-edge` | Auto-restart after 10s |
| After `sudo reboot` | Both services auto-start |

## Notes

- **Do NOT modify** the Virtual Factory config path — it's already correct on VPS
- **Do NOT modify** the Edge Agent config.yaml — it's already deployed with 26 OPC UA tags
- Use `sudo systemctl` (not just `systemctl`) on VPS
- Log rotation sẽ được thêm sau (Phase 7), hiện tại log append vào 1 file
