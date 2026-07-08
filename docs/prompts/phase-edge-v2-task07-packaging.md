# E2V2-5: Packaging + restart_agent

## Context

Edge v2 must become installable as a real product. This phase creates Docker Compose and systemd packaging, including the `restart_agent` command that relies on the supervisor (Docker restart policy / systemd Restart=on-failure). Also adds config backup/restore, support bundle download, and a one-command install script.

## Plan Reference

- `docs/phase-edge-v2-productization-plan.md` §14
- `docs/01-project-constitution.md`
- `docs/19-deployment-design.md`

## Constitution Checklist

- [x] Installation must not require manual steps beyond prerequisites
- [x] restart_agent uses only supervisor mechanism (no self-modifying code)
- [x] Config backup/restore must be secure (no secrets in support bundle)
- [x] Target hardware profile documented

## Implementation Checklist

### Docker Compose

- [ ] **5.1** Create `edge-v2/Dockerfile`:
  ```dockerfile
  FROM python:3.11-slim
  WORKDIR /app
  COPY requirements.txt .
  RUN pip install --no-cache-dir -r requirements.txt
  COPY agent/ ./agent/
  COPY console/ ./console/
  EXPOSE 8011
  HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:8011/api/status || exit 1
  CMD ["python", "-m", "agent.main"]
  ```

- [ ] **5.2** Create `edge-v2/docker-compose.edge-v2.yml`:
  ```yaml
  services:
    plantos-edge-v2:
      build: .
      container_name: plantos-edge-v2
      ports: ["8011:8011"]
      volumes:
        - ./config:/app/config
        - edge-v2-data:/app/data
      restart: unless-stopped
      environment:
        - EDGE_CONFIG_PATH=/app/config/edge.yaml
  volumes:
    edge-v2-data:
  ```

### systemd

- [ ] **5.3** Create `edge-v2/plantos-edge-v2.service`:
  ```ini
  [Unit]
  Description=PlantOS Edge Lite v2
  After=network.target
  [Service]
  Type=simple
  User=plantos
  WorkingDirectory=/opt/plantos-edge-v2
  ExecStart=/opt/plantos-edge-v2/venv/bin/python -m agent.main
  Restart=on-failure
  RestartSec=10
  Environment=EDGE_CONFIG_PATH=/etc/plantos-edge-v2/config.yaml
  [Install]
  WantedBy=multi-user.target
  ```

### Installer

- [ ] **5.4** Create `edge-v2/install.sh`:
  - Check prerequisites (Python 3.11+, pip)
  - Create plantos user if not exists
  - Create directories, copy files
  - Create venv, install dependencies
  - Run first-time setup wizard if no config exists
  - Install & enable systemd service
  - Print success message with next steps

### restart_agent Command

- [ ] **5.5** Implement `restart_agent` command handler in `edge-v2/agent/commands/handlers.py`:
  ```python
  async def handle_restart_agent(self, command: Command) -> CommandResult:
      # 1. Flush buffer (sync pending measurements)
      await self.sync.flush()
      # 2. Stop all connectors gracefully
      await self.connectors.stop_all()
      # 3. Report "executing" to Center
      await self.commands.report(command.id, status="executing")
      # 4. Exit with code 0
      # 5. Supervisor (Docker/systemd) brings process back
      sys.exit(0)
  ```

- [ ] **5.6** Register `restart_agent` in ALLOWED_COMMANDS (only if running under supervisor):
  - Detect supervisor: check if running in Docker (`/proc/1/cgroup`) or systemd (`journalctl`)
  - If no supervisor detected: command returns error "restart_agent requires Docker or systemd supervisor"

### Center — Enable restart_agent Button

- [ ] **5.7** Update `EdgeDetailPage.tsx`:
  - Enable [Restart Agent] button
  - Remove "Available after packaging" tooltip
  - Add confirmation dialog: "Restarting the agent will cause a brief interruption. Continue?"

- [ ] **5.8** Add `restart_agent` to ALLOWED_COMMANDS in Center:
  ```python
  "restart_agent": {"description": "Restart the Edge agent (requires Docker/systemd)", "requires_target": False}
  ```

### Config Backup/Restore

- [ ] **5.9** Implement `/api/config/backup`:
  - Create timestamped backup of config.yaml
  - Store in `edge-v2/config/backups/`
  - Return backup file path

- [ ] **5.10** Implement `/api/config/restore`:
  - Accept backup file path
  - Validate backup is valid YAML
  - Restore config, restart/reload connectors
  - Create backup of current config before restoring

### Support Bundle

- [ ] **5.11** Implement `/api/support/bundle`:
  - Download ZIP containing:
    - Sanitized config (no passwords/keys)
    - Recent logs (last 1 hour)
    - Version info
    - Connector status snapshot
    - Metrics snapshot (CPU, RAM, disk, backlog)
  - Sanitize: strip all secrets, passwords, API keys, hashes

### Version Endpoint

- [ ] **5.12** Implement `/api/version`:
  ```json
  {
    "version": "2.0.0-dev",
    "build_date": "2026-07-08",
    "python_version": "3.11.x",
    "dependencies": {"duckdb": "0.9.x", "aiohttp": "3.9.x"}
  }
  ```

### Healthcheck

- [ ] **5.13** Ensure `/api/status` works for Docker healthcheck:
  - Return 200 if agent is running
  - Return 503 if critical failure (buffer not accessible, all connectors down)
  - No auth required on this endpoint

### Documentation

- [ ] **5.14** Create `edge-v2/INSTALL.md`:
  - Prerequisites
  - Docker install steps
  - systemd install steps
  - First-run setup
  - Troubleshooting

- [ ] **5.15** Create `edge-v2/UPGRADE.md`:
  - Backup config
  - Pull new version
  - Restore config
  - Verify

### Tests

- [ ] **5.16** Docker Compose install test on clean Ubuntu 22.04 VM:
  - `docker compose up -d` → agent starts
  - `curl http://localhost:8011/api/status` → 200
  - `curl http://localhost:8011/api/version` → version info
  - `docker restart plantos-edge-v2` → agent recovers
  - `docker compose down && docker compose up -d` → data survives

- [ ] **5.17** systemd install test on clean Ubuntu 22.04:
  - `sudo ./install.sh` → completes without errors
  - `systemctl status plantos-edge-v2` → active (running)
  - `systemctl restart plantos-edge-v2` → agent restarts
  - Reboot → agent starts automatically

- [ ] **5.18** restart_agent command test:
  - Create restart_agent command from Center
  - Edge polls, executes, exits
  - Supervisor brings it back
  - Edge reports success on next poll

- [ ] **5.19** Config backup/restore test:
  - Backup config → modify → restore → verify original restored
  - Support bundle → verify no secrets in ZIP
  - Sanitized config export → verify no passwords

## Files to Create

```
edge-v2/
  Dockerfile
  docker-compose.edge-v2.yml
  plantos-edge-v2.service
  install.sh
  INSTALL.md
  UPGRADE.md

edge-v2/agent/web/routes/
  backup.py
  support.py
```

## Files to Modify

```
edge-v2/agent/main.py — add restart_agent handler, supervisor detection
edge-v2/agent/commands/handlers.py — add handle_restart_agent
backend/app/modules/edge_nodes/commands.py — add restart_agent to ALLOWED_COMMANDS
frontend/src/features/edge-fleet/EdgeDetailPage.tsx — enable restart button
```

## Acceptance Criteria

```text
✅ Docker Compose: `docker compose up -d` → agent running on port 8011
✅ systemd: `sudo ./install.sh` → service active, starts on boot
✅ restart_agent command works via Docker restart policy
✅ restart_agent command works via systemd Restart=on-failure
✅ Config backup/restore cycle works (modify → restore → verified)
✅ Support bundle downloads with sanitized config
✅ Version endpoint returns correct version
✅ Healthcheck works for Docker (docker ps shows healthy)
✅ Reboot recovery: data and config survive restart
✅ Fresh install on clean Ubuntu completes in <30 minutes
✅ Installation documentation is clear and tested
```

## Red Flags

- Stop if: restart_agent is implemented as in-process restart (must use supervisor)
- Stop if: support bundle contains plaintext passwords or API keys
- Stop if: Docker image size >500MB (should be <200MB with slim base)
- Stop if: constitution violation (installer modifies anything outside /opt/plantos-edge-v2)
