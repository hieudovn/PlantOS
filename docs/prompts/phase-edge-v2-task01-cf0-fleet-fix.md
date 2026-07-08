# CF-0: Center Fleet Baseline Fix

## Context

PlantOS Center's Edge Fleet page is broken. The backend uses an in-memory `_edge_nodes: dict` instead of the PostgreSQL `edge_nodes` table. The frontend calls `getEdgeNodes` which is not defined in `api.ts`. The `edge.heartbeat` event subscriber is never registered in `main.py`. This must be fixed **before** any Edge v2 work begins.

## Plan Reference

- `docs/phase-edge-v2-productization-plan.md` §11.1, §16
- `docs/01-project-constitution.md`
- `docs/60-edge-center-strategy.md`

## Constitution Checklist

- [x] Does NOT bypass UNS/CDM
- [x] Does NOT bind UI to raw PLC tags
- [x] Does NOT let UI query storage directly
- [x] Maintains Edge/Center separation
- [x] Does NOT break existing Edge v1 flow
- [x] Backward-compatible with Edge v1 heartbeat format

## Implementation Checklist

### Center Backend

- [ ] **CF-0.1** Refactor `receive_heartbeat` in `backend/app/modules/edge_nodes/router.py`:
  - Remove `_edge_nodes: dict[str, dict] = {}` module-level dict
  - Upsert into `EdgeNode` SQLAlchemy model (edge_node_id, status, last_heartbeat)
  - Keep backward-compatible: accept all existing heartbeat fields
  - Store hostname, ip_address, edge_version if present in payload

- [ ] **CF-0.2** Refactor `GET /edge-nodes` in `backend/app/modules/edge_nodes/router.py`:
  - Query `EdgeNode` table from PostgreSQL
  - Return list of edge nodes with status, last_heartbeat, hostname, ip_address, edge_version
  - Handle empty table gracefully (return `[]`)

- [ ] **CF-0.3** Add nullable columns to `EdgeNode` model in `backend/app/modules/edge_nodes/models.py`:
  - `hostname: str | None` (VARCHAR 255)
  - `ip_address: str | None` (VARCHAR 45)
  - `edge_version: str | None` (VARCHAR 32)
  - All nullable, default None

- [ ] **CF-0.4** Create Alembic migration for new columns:
  - `alembic revision --autogenerate -m "add_edge_node_hostname_ip_version"`
  - Verify migration is safe (nullable, no data loss)
  - Run `alembic upgrade head`

- [ ] **CF-0.5** Register `edge.heartbeat` subscriber in `backend/app/main.py`:
  - In `_register_event_subscribers()`, add: `event_dispatcher.subscribe("edge.heartbeat", on_edge_heartbeat)`
  - Verify `on_edge_heartbeat` is imported from `app.modules.events.subscribers`

### Frontend

- [ ] **CF-0.6** Add `getEdgeNodes` to `frontend/src/lib/api.ts`:
  ```typescript
  export async function getEdgeNodes(): Promise<EdgeNode[]> {
    const response = await fetch(`${BASE_URL}/api/v1/edge-nodes`, {
      headers: getAuthHeaders(),
    });
    if (!response.ok) throw new Error('Failed to fetch edge nodes');
    return response.json();
  }
  ```
  Add `EdgeNode` type interface with fields: edge_node_id, node_type, status, last_heartbeat, hostname, ip_address, edge_version.

- [ ] **CF-0.7** Fix `EdgeFleetPage.tsx`:
  - Fix import: `import { getEdgeNodes } from '@/lib/api';`
  - Verify `getEdgeNodes` is correctly imported (currently broken)
  - Add proper TypeScript types

- [ ] **CF-0.8** Replace hardcoded KPI in `EdgeFleetPage.tsx`:
  - Change `value="1"` to `value={edgeNodes.length}`
  - Make table data dynamic from API response
  - Keep `refetchInterval: 5000` for polling

### Tests

- [ ] **CF-0.9** Verify Edge v1 heartbeat persists:
  - Send heartbeat via curl to `POST /api/v1/edge-nodes/heartbeat`
  - Restart Center backend
  - Verify `GET /api/v1/edge-nodes` still returns the edge node
  - Previously this would return empty (in-memory loss)

- [ ] **CF-0.10** Verify frontend renders:
  - Open `/edge` page in Center
  - Verify edge nodes appear in table
  - Verify KPI shows correct count
  - Verify no console errors about `getEdgeNodes is not a function`

## Files to Create

None (modify existing only)

## Files to Modify

- `backend/app/modules/edge_nodes/router.py` — persist to DB
- `backend/app/modules/edge_nodes/models.py` — add columns
- `backend/migrations/versions/` — new migration
- `backend/app/main.py` — register subscriber
- `frontend/src/lib/api.ts` — add getEdgeNodes
- `frontend/src/features/edge-fleet/EdgeFleetPage.tsx` — fix imports + dynamic data

## Red Flags

- Stop if: heartbeat endpoint breaks Edge v1 format
- Stop if: migration is not nullable (could fail on existing data)
- Stop if: changing `_edge_nodes` dict breaks sync/manifest endpoint
