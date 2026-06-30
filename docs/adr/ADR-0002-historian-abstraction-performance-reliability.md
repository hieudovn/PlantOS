# ADR-0002: Historian Abstraction, Performance and Reliability Strategy

## Status

Accepted

## Date

2026-06-30

## Context

PlantOS accepts TDengine as the MVP built-in historian backend in ADR-0001. However, PlantOS must remain able to replace TDengine with another open-source TSDB, community edition, or commercial historian/product in the future.

The concern is that excessive modularization or abstraction may reduce reliability, stability or data performance.

This ADR defines how PlantOS should keep the historian backend replaceable without turning the abstraction layer into a performance bottleneck.

## Decision

PlantOS shall implement a thin, performance-aware Historian Service Interface.

TDengine is a backend adapter, not the core architecture.

```text
PlantOS API / Rule / Visualization / MES / AI
        ↓
Historian Service Interface
        ↓
Backend-specific Adapter
        ↓
TDengine / other TSDB / external historian
```

No module except the backend-specific adapter may depend directly on TDengine schema, TDengine SQL, TDengine driver, TDengine connection method, TDengine table naming or TDengine-specific query behavior.

## Performance principle

The abstraction must be thin and batch-oriented.

Allowed:

```text
write_measurements(batch)
get_latest(signal_ids)
query_history(signal_id, from, to, interval, aggregation)
query_multi_signal_history(signal_ids, from, to, interval, aggregation)
health_check()
get_capabilities()
```

Avoid:

```text
write_one_point_per_call()
query_one_signal_per_widget_without_cache()
generic SQL passthrough from UI/rule engine
forcing all historian backends to behave identically
large object mapping per data point
```

## Reliability principle

Historian backend failure must not crash the whole PlantOS platform.

Required design:

- ingestion queue/buffer before historian writes,
- retry policy,
- dead-letter or failed batch tracking,
- idempotent write strategy where possible,
- health check and degraded mode,
- clear error reporting to Edge/Center UI,
- backup/restore strategy for built-in historian mode,
- external historian connector health status for integration mode.

## Backend capability model

Every historian adapter must expose capabilities.

Example:

```json
{
  "backend": "tdengine",
  "supports_write": true,
  "supports_batch_write": true,
  "supports_latest_query": true,
  "supports_aggregation": true,
  "supports_downsampling": true,
  "supports_backfill": true,
  "supports_string_values": false,
  "supports_quality": true,
  "supports_external_tag_mapping": false
}
```

PlantOS must not assume all historian backends have identical capabilities.

## Data model boundary

PlantOS owns:

- asset_id,
- signal_id,
- signal_name,
- engineering_unit,
- quality,
- UNS path,
- CDM mapping,
- visualization binding.

Historian backend owns:

- physical table/supertable layout,
- query language,
- write protocol,
- internal compression,
- retention implementation,
- cluster/replication mechanism.

## TDengine MVP design guardrails

For TDengine MVP:

- use TDengine as an external service,
- do not fork or modify TDengine source code,
- use official supported connector path,
- prefer WebSocket connector path where practical for future compatibility,
- avoid REST dependency as a long-term design,
- use batch writes,
- keep TDengine schema inside `TDengineHistorianAdapter`,
- keep metadata in PostgreSQL, not TDengine,
- create benchmark scripts before claiming production readiness.

## Performance validation requirements

Before PlantOS is used beyond demo/MVP, benchmark:

- points per second ingestion,
- batch size impact,
- query latency for current values,
- query latency for historical trends,
- multi-signal query performance,
- retention and disk usage,
- restart/recovery behavior,
- network interruption behavior,
- edge backlog flush behavior,
- concurrent UI/dashboard load.

## Target MVP performance assumptions

MVP should optimize for correctness and architecture first, but must not introduce obvious anti-patterns.

Minimum expectations:

- ingestion API accepts batched measurements,
- UI queries go through backend APIs,
- trend API supports time range and interval parameters,
- simulator can generate enough data to test continuous ingestion,
- historian adapter can later be replaced without rewriting frontend or business modules.

## Alternatives considered

### Direct TDengine usage everywhere

Pros:

- fastest initial implementation,
- fewer code layers.

Cons:

- high lock-in,
- hard replacement,
- UI/rule/MES/AI coupling to TDengine,
- license and operational risk spread across codebase.

Rejected.

### Heavy generic data access abstraction

Pros:

- theoretically supports many databases.

Cons:

- may hide important TSDB-specific performance capabilities,
- may create slow generic queries,
- may force lowest-common-denominator design.

Rejected.

### Thin historian adapter interface

Pros:

- replaceable backend,
- controlled performance,
- clear module boundary,
- allows backend-specific optimization inside adapter.

Cons:

- requires careful interface design,
- not all backend features can be exposed uniformly.

Accepted.

## Consequences

Positive:

- TDengine can be replaced later.
- UI, MES, AI and rule engine remain stable.
- Performance-critical logic remains close to backend adapter.
- PlantOS can support built-in, external, hybrid and pass-through historian modes.

Negative / trade-offs:

- More design discipline is required.
- Adapter tests and benchmarks are required.
- Some backend-specific features may not be immediately exposed.

## Review date

After Phase 1 MVP benchmark and before pilot/customer deployment.

## Notes

Any future historian backend must implement the same logical contract or explicitly document unsupported capabilities.
