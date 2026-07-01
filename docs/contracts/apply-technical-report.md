# Apply Endpoint — Technical Report

**Endpoint:** `POST /api/v1/contracts/apply`
**Phase:** 7-03 (Phase D) | **Status:** Implemented
**Depends on:** 7-01 (Validator), 7-02 (Preview)

---

## Transaction Boundary

Each entity type (plants, areas, assets, signals) is committed in a separate transaction:

```
BEGIN (plants) → CREATE/UPDATE → COMMIT
BEGIN (areas)  → CREATE/UPDATE → COMMIT
BEGIN (assets) → CREATE/UPDATE → COMMIT
BEGIN (signals)→ CREATE/UPDATE → COMMIT
```

**Rationale:** Partial success is preferred over full rollback. If asset creation fails, the plant and areas are already persisted. This avoids orphaned data where possible while allowing forward progress.

## Rollback Behavior

- **No automatic rollback** across entity types. Each type commits independently.
- If a specific entity write fails, that entity is skipped (on_conflict=skip) or the entire apply aborts (on_conflict=fail).
- No data written in previous transactions is rolled back.

## Conflict Handling

| on_conflict | Behavior |
|---|---|
| `fail` | Abort apply immediately, return error |
| `skip` | Skip conflicting entity, continue with next |
| `update` | Update existing entity (only if allow_update_existing=true) |

## Idempotency

Apply with `on_conflict=skip` is idempotent:
- First apply: creates all entities
- Second apply with same contract: all entities skipped (already exist)
- Result: no duplicate data, no errors

Apply with `on_conflict=fail` is NOT idempotent:
- First apply: creates entities
- Second apply: aborts with conflict error

## Orphan Handling

| orphaned_action | Behavior |
|---|---|
| `report` (default) | List orphaned entities in response, no DB changes |
| `deactivate` | Set `status='deprecated'` on orphaned entities |
| `delete` | Hard delete (requires explicit allow_delete_missing=true) |

## Repository/Service Usage

| Entity | Read | Write |
|---|---|---|
| Plant | `PlantRepository` | ORM model (`Plant` instance + `session.add()`) |
| Area | Raw SQL — no dedicated repository method | ORM model (`Area` instance + `session.add()`) |
| Asset | `AssetRepository.get_by_id()` | ORM model (`Asset` instance + `session.add()`) |
| Signal | `SignalRepository.get_by_id()` | ORM model (`Signal` instance + `session.add()`) |

**Note:** Raw SQL via `text()` is used for FK UUID lookups (resolving string business keys like `area_id` → `area_id_fk` UUID). Writes use SQLAlchemy ORM model constructors which handle all column defaults (`created_at`, `updated_at`, `source_type`, etc.).

## Safety Guarantees

1. **Default safest**: `on_conflict=fail`, no deletes, no silent overwrites
2. **Import policy from request body** — not from contract, preventing contract author from setting dangerous policies
3. **`orphaned_action='delete'` requires explicit `allow_delete_missing=true`**
4. **`mode != 'apply'` rejected** with 400 error
5. **Validator runs first** — invalid contracts are rejected before any DB write
