# ADR-0006: Operational Model Import Contract v2 & Model Importer Architecture

## Status

Proposed

## Context

PlantOS currently has an Integration Data Contract (`examples/vf-plantos-contract.yaml`, v1.0) that serves as the single source of truth for the Virtual Factory Compressor Train model. However, the contract has architectural limitations:

1. **VF-specific fields leak into core signal definitions** — `opcua_node_id`, `vf_internal_ref`, `vf_sensor_id` are embedded in every signal, coupling PlantOS CDM to Virtual Factory internals
2. **No separation of concerns** — core operational model (plant/area/asset/signal) is mixed with source-system bindings and simulation behaviors
3. **No formal schema** — validation is manual (checklist in markdown), error-prone
4. **No import governance** — no validate → preview → apply pipeline, no conflict resolution policy
5. **Single-source hardcoded** — cannot support SCADA, MES, CSV, or manual contract sources

## Decision

### 1. Contract v2 — Separate Core from Extensions

The contract is restructured into **core** (always required) and **extensions** (optional, source-system-specific):

```
Core:    contract, source, plant, areas, assets, signals, uns, import_recommendation
Ext:     bindings.{opcua,mqtt,modbus}, simulation.behaviors, extensions.{}
```

Core signal definition no longer includes `opcua_node_id`, `vf_internal_ref`, or `vf_sensor_id`. These are moved to `bindings.opcua[]`, `simulation.behaviors`, and `extensions.vf_sensor_refs` respectively.

### 2. JSON Schema for Structural Validation

A machine-readable JSON Schema (`schemas/plantos-integration-contract.schema.json`) enforces:
- Required fields and types
- Naming conventions (regex patterns for IDs)
- Enum values (asset_type, criticality, status, engineering_unit)
- Format validation (semver, ISO 8601, OPC UA NodeId pattern)

### 3. Phased Importer Architecture

```
Phase B: POST /api/v1/contracts/validate   → structural + cross-reference validation
Phase C: POST /api/v1/contracts/preview     → diff against current DB state
Phase D: POST /api/v1/contracts/apply       → execute import
Phase E: POST /api/v1/contracts/generate/*  → manifest generation
```

Each phase builds on the previous. No phase proceeds without gate review.

### 4. Import Policy Controlled by API Caller

`import_policy` is NOT embedded in the contract YAML. The contract only provides `import_recommendation` as a hint. The actual policy (mode, on_conflict, orphaned_action) is specified by the API caller at import time. Default: `validate_only` + `fail` + `report` (safest).

### 5. Orphaned Entity Handling

When importing a contract against an existing plant, entities in the database but NOT in the contract are "orphaned". Default action: `report` (list in response, no DB changes). Supported future actions: `deactivate` (set status=deprecated), `delete` (requires explicit flag).

### 6. UNS Path Generation

UNS paths are generated algorithmically from contract entities, not manually specified. The validator generates paths and returns them in response for verification.

## Consequences

### Positive

- PlantOS CDM no longer coupled to Virtual Factory internals
- Any source system (SCADA, MES, CSV) can produce a valid contract
- JSON Schema enables automated validation in CI/CD
- Phased importer is safe by default — validate_first, apply_later
- Orphaned detection prevents silent data loss

### Negative

- Existing v1 contract must be migrated to v2 format (one-time effort)
- Edge Agent config currently has OPC UA tags inline — will need to read from `bindings.opcua[]` in future
- Seed script must support both v1 and v2 formats during transition

### Migration Path

1. v2 contract exists alongside v1 (not replacing immediately)
2. Seed script detects version and handles both
3. Edge Agent continues using config.yaml `tags` independently
4. Future: Edge Agent reads `bindings.opcua[]` from contract via Center API

## References

- `docs/contracts/plantos-integration-contract-spec.md` — Full v2 specification
- `schemas/plantos-integration-contract.schema.json` — JSON Schema
- `examples/contracts/vf-compressor-train.contract.yaml` — Example v2 contract
- `docs/adr/ADR-0005-integration-contract.md` — Previous contract ADR (v1)
