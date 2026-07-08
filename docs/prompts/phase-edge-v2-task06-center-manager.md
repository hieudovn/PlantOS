# E2V2-4: Center Edge Manager Lite

## Context

The Center's edge fleet management must become persistent and support basic remote actions. CF-0 already wired the `edge_nodes` table and fixed the frontend. This phase adds new tables for heartbeats, connectors, commands, and config versions. It implements a pull-based command queue so the Center can trigger sync_now, reload_config, and restart_connector on Edge v2 — no restart_agent yet (that requires supervisor, E2V2-5). Also adds an Edge Detail page to the Center UI.

## Plan Reference

- `docs/phase-edge-v2-productization-plan.md` §11
- `docs/01-project-constitution.md`
- `docs/60-edge-center-strategy.md`

## Constitution Checklist

- [x] Edge/Center responsibilities remain separate
- [x] No unsafe remote commands (allowlist only)
- [x] Pull-based — Edge polls Center (no inbound connectivity needed)
- [x] All command execution is audited
- [x] Backward-compatible with Edge v1 heartbeat
- [x] Persistent storage (not in-memory)

## Implementation Checklist

### Database

- [ ] **4.1** Create Alembic migration for new tables:
  - `edge_heartbeats` — history of all heartbeats
  - `edge_connectors` — per-connector status
  - `edge_commands` — command queue
  - `edge_config_versions` — config version tracking
  - See plan §11.2 for full DDL

- [ ] **4.2** Create SQLAlchemy models in `backend/app/modules/edge_nodes/models.py`:
  - `EdgeHeartbeat`
  - `EdgeConnector`
  - `EdgeCommand`
  - `EdgeConfigVersion`
  - All with proper relationships to `EdgeNode`

- [ ] **4.3** Add columns to `EdgeNode` (if not done in CF-0):
  - `hostname`, `ip_address`, `edge_version` (nullable)
  - `capabilities` (JSONB, default `[]`)
  - `workspace_id` (VARCHAR 128, nullable)

### Heartbeat Enhancement

- [ ] **4.4** Refactor `receive_heartbeat` in `backend/app/modules/edge_nodes/router.py`:
  - Accept both v1 (minimal) and v2 (extended) heartbeat formats
  - v1: `{edge_node_id, status, backlog_count, hostname, ip_address, signal_count, version}`
  - v2: above + `{center_sync, disk_usage_mb, capabilities, connectors: [{connector_id, type, status, signal_count, last_error}]}`
  - Upsert `EdgeNode` with all available fields
  - Insert `EdgeHeartbeat` record
  - Upsert `EdgeConnector` records from heartbeat payload
  - Dispatch `edge.heartbeat` event

### API Endpoints

- [ ] **4.5** `GET /api/v1/edge-nodes` — list all (already working from CF-0, verify)
- [ ] **4.6** `GET /api/v1/edge-nodes/{edge_node_id}` — detail:
  - Return edge_node fields + latest heartbeat + connector list + recent command count

- [ ] **4.7** `GET /api/v1/edge-nodes/{edge_node_id}/connectors` — connector status list
- [ ] **4.8** `GET /api/v1/edge-nodes/{edge_node_id}/heartbeats` — recent heartbeats (last 100, paginated)
- [ ] **4.9** `POST /api/v1/edge-nodes/{edge_node_id}/commands` — create command:
  - Validate command_type against ALLOWED_COMMANDS
  - Validate target for restart_connector (connector_id must exist)
  - Return command with status "pending"

- [ ] **4.10** `GET /api/v1/edge-nodes/{edge_node_id}/commands/pending` — poll:
  - Return commands with status "pending", ordered by created_at
  - Mark returned commands as "executing" atomically

- [ ] **4.11** `POST /api/v1/edge-nodes/{edge_node_id}/commands/{cmd_id}/result` — report result:
  - Update status to "success" or "failed"
  - Set finished_at, result_message

- [ ] **4.12** `GET /api/v1/edge-nodes/{edge_node_id}/commands` — history (last 100, paginated)

### Allowed Commands (E2V2-4)

- [ ] **4.13** Define allowed commands in `backend/app/modules/edge_nodes/commands.py`:
  ```python
  ALLOWED_COMMANDS = {
      "sync_now": {"description": "Trigger immediate sync flush", "requires_target": False},
      "reload_config": {"description": "Reload config from YAML", "requires_target": False},
      "restart_connector": {"description": "Restart a connector", "requires_target": True},
      "enable_connector": {"description": "Enable a disabled connector", "requires_target": True},
      "disable_connector": {"description": "Disable a running connector", "requires_target": True},
  }
  # NO restart_agent here — that's E2V2-5
  ```

### Offline Detection

- [ ] **4.14** Implement offline detection background task:
  ```python
  # backend/app/core/edge_offline_detector.py
  async def detect_offline_edges():
      """Runs every 30s. Marks edges offline if no heartbeat in 60s."""
  ```
  - Register as FastAPI lifespan background task
  - Status transitions: online → stale (30s) → offline (60s)
  - Dispatch `edge.offline` event on transition

### Edge v2 — Command Poller

- [ ] **4.15** Implement `CommandPoller` in `edge-v2/agent/commands/poller.py`:
  - Poll `GET /api/v1/edge-nodes/{node_id}/commands/pending` every N seconds
  - Execute allowed commands locally
  - Report result via `POST /api/v1/edge-nodes/{node_id}/commands/{cmd_id}/result`

- [ ] **4.16** Implement command handlers in `edge-v2/agent/commands/handlers.py`:
  - `handle_sync_now()` — call `self.sync.flush()` immediately
  - `handle_reload_config()` — reload config from YAML, re-validate all connectors
  - `handle_restart_connector(connector_id)` — stop + start specific connector
  - `handle_enable_connector(connector_id)` — enable disabled connector
  - `handle_disable_connector(connector_id)` — disable running connector

### Frontend — Edge Detail Page

- [ ] **4.17** Add API functions to `frontend/src/lib/api.ts`:
  - `getEdgeNode(edgeNodeId)` — GET `/api/v1/edge-nodes/{id}`
  - `getEdgeConnectors(edgeNodeId)` — GET `/api/v1/edge-nodes/{id}/connectors`
  - `getEdgeCommands(edgeNodeId)` — GET `/api/v1/edge-nodes/{id}/commands`
  - `createEdgeCommand(edgeNodeId, commandType, target?)` — POST `/api/v1/edge-nodes/{id}/commands`

- [ ] **4.18** Create `EdgeDetailPage.tsx`:
  - Overview card: status, version, hostname, IP, signals, backlog, disk
  - Connectors table: connector_id, type, status, signal_count, [Restart] button
  - Commands section: [Sync Now] [Reload Config] buttons
  - [Restart Agent] button — DISABLED with tooltip "Available after Edge v2 packaging (E2V2-5)"
  - Command history table
  - Recent heartbeats table

- [ ] **4.19** Add route in `frontend/src/routes/index.tsx`:
  - `/edge/:edgeNodeId` → `EdgeDetailPage`
  - Click on edge node row in EdgeFleetPage → navigate to detail

### Tests

- [ ] **4.20** Heartbeat persistence tests:
  - Send v1 heartbeat → verify persist
  - Send v2 heartbeat → verify persist with all fields
  - Restart Center → verify data survives

- [ ] **4.21** Backward compatibility tests:
  - Edge v1 heartbeat still works after all changes
  - Edge v1 sync/manifest flow unchanged

- [ ] **4.22** Command queue E2E tests:
  - Create command → poll → execute → report → verify audit
  - Invalid command type → rejected
  - Command with missing target → rejected

- [ ] **4.23** Offline detection tests:
  - Edge stops sending heartbeats → status goes stale → offline
  - Edge resumes → status goes back to online

## Files to Create

```
backend/migrations/versions/0XX_edge_v2_tables.py
backend/app/modules/edge_nodes/commands.py
backend/app/core/edge_offline_detector.py

edge-v2/agent/commands/
  __init__.py
  poller.py
  handlers.py

frontend/src/features/edge-fleet/EdgeDetailPage.tsx
```

## Files to Modify

```
backend/app/modules/edge_nodes/
  models.py         — add EdgeHeartbeat, EdgeConnector, EdgeCommand, EdgeConfigVersion
  router.py         — add new endpoints, enhance heartbeat

backend/app/main.py — register offline detector

frontend/src/lib/api.ts — add edge detail/command API functions
frontend/src/routes/index.tsx — add /edge/:edgeNodeId route
frontend/src/features/edge-fleet/EdgeFleetPage.tsx — link rows to detail

edge-v2/agent/main.py — wire CommandPoller
```

## Acceptance Criteria

```text
✅ Edge v2 heartbeat persists in PostgreSQL with connector info
✅ Edge detail page in Center shows health, connectors, commands
✅ sync_now command works end-to-end (Center → Edge → result)
✅ reload_config command works (config reloaded, connectors re-validated)
✅ restart_connector command works for individual connectors
✅ enable/disable_connector commands work
✅ [Restart Agent] button is disabled with clear "why" tooltip
✅ Command audit trail visible in Center (history with timestamps)
✅ Offline detection marks stale edges correctly
✅ Edge v1 heartbeat still works (backward compatibility)
✅ Edge v1 sync/heartbeat flow unchanged
```

## Red Flags

- Stop if: any command allows arbitrary shell execution
- Stop if: restart_agent is implemented without supervisor
- Stop if: migration is not backward-compatible with existing edge_nodes table
- Stop if: constitution violation (Center directly reaching into Edge)
