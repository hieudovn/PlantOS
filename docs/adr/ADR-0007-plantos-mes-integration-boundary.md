# ADR-0007: PlantOS–MES Integration Boundary

> **Status:** ACCEPTED  
> **Date:** 2026-07-06  
> **Deciders:** Solution Architect, PM-Designer PlantOS

---

## Context

PlantOS is being prepared for integration with a Manufacturing Execution System (MES). The SA has defined the integration boundary and required PlantOS to upgrade its semantic core (asset hierarchy, signal registry, UNS topic policy, runtime events) without becoming an MES subsystem.

## Decision

### 1. PlantOS publishes. MES interprets.

PlantOS is the source of truth for asset/signal/telemetry data. MES is the source of truth for production context (work orders, BOMs, operations, products). Neither system models the other's domain.

### 2. PlantOS must NOT model MES concepts

PlantOS must never contain:
- `work_order_id`, `manufacturing_order_id`
- `operation_code`, `product_code`, `checklist_id`
- `material_lot_id`, `BOM_id`, `routing_id`
- Any MES-specific identifiers in core data model or contract

### 3. Asset hierarchy supports flexible depth

PlantOS supports Plant → Area → [Line/Unit] → [Cell/Group] → Equipment → [Subsystem] → Signal. Depth is configurable per plant, not enforced. Minimum 3 levels. Warning above 6.

### 4. `asset_role` is mandatory for new contracts

Every asset declares its semantic role: `functional_location`, `equipment`, `subsystem`, `component`, or `logical_group`. Existing contracts auto-derive from `asset_type`.

### 5. `signal_category` replaces single-value `signal_type`

Signal categories: `measurement`, `status`, `alarm`, `counter`, `calculated`, `command`. Backward compatible with old `signal_type: measurement`.

### 6. UNS topics are derived, not stored

UNS topic: `plantos/{plant}/{area}/{asset}/{category}/{signal_name}`. Computed deterministically from data model. Never manually authored or stored.

### 7. Runtime events do not carry MES context

Event envelope includes: `event_id`, `correlation_id` (optional), `event_type`, `timestamp`, `asset.*`, `signal.*`, `uns_topic`, `payload`. No production context fields.

### 8. MES mapping contract is MES-owned

PlantOS exports identifier surface (plant_id, area_id, asset_id, signal_id, etc.). MES maintains its own mapping contract. PlantOS does not store, validate, or consume MES identifiers.

### 9. Integration phases

```
Phase 9A: Contract & Schema Upgrade (asset_role, signal_category)
Phase 9B: DB Migration + API Update
Phase 9C: UNS Topic Policy
Phase 9D: Runtime Event Contract (deferred until SA review)
Phase 9E: MES Integration Readiness Report
```

## Consequences

- PlantOS contract v2.0+ requires `asset_role` and supports `signal_category`
- Backend API exposes new fields without breaking existing consumers
- UNS topics are always consistent because they're derived
- MES team must build their own mapping contract
- PlantOS runtime events will NOT contain WO context — MES must enrich internally
