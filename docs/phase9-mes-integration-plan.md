# PlantOS PM Plan — Semantic Core / UNS / CDM Upgrade for MES Integration

> **Author:** PM-Designer | **Date:** 2026-07-06  
> **Source:** SA Proposal "Chuẩn bị Semantic Core / UNS / CDM cho tích hợp MES"  
> **Status:** SA APPROVED WITH MINOR MODIFICATIONS (2026-07-06)  
> **Next:** Phase 9A can start immediately. Phase 9D after event contract update.

---

## 0. SA Review Modifications (incorporated)

The SA approved the plan with 8 modifications. These are now reflected below:

| # | Modification | Section |
|---|-------------|--------|
| 1 | Add optional `correlation_id` to event envelope | §6.2 |
| 2 | Define event-specific required payload per event type | §6.3 |
| 3 | `external_refs` is NOT integration source of truth; MES maps separately | §4.5 |
| 4 | MES mapping lives in a separate mapping contract (PlantOS does not own it) | §5.5 |
| 5 | Define QoS policy by event type | §6.5 |
| 6 | Future batch envelope — documentation only, not implemented now | §6.6 |
| 7 | UNS topic is derived/computed — not manually authored | §5.4 |
| 8 | Add runtime event validation examples | §7.3 |

---

## 1. Understanding of SA Direction

The SA proposal correctly defines the boundary:

```
PlantOS = Operational Asset / Signal / Telemetry Platform
MES     = Manufacturing Execution / Production Context Platform

PlantOS publishes. MES interprets.
```

**Agreement:** This boundary is correct and must be rigidly enforced. PlantOS should never model Work Orders, BOMs, operations, or production context. Any feature request that requires PlantOS to "know" MES context should be rejected or redirected to an integration layer.

---

## 2. Current PlantOS Contract Assessment

### 2.1 What already exists

| Capability | Status | Maturity |
|-----------|--------|----------|
| Plant / Area / Asset hierarchy | ✅ In contract v1.0 | Production |
| Signal registry with asset binding | ✅ In contract v1.0 | Production |
| OPC UA binding extension | ✅ In contract v1.0 | Production |
| Asset type vocabulary | ✅ `compressor_train`, `pump`, `motor`, etc. | Partial — needs `asset_role` |
| Naming conventions | ✅ Documented in contract spec | Stable |
| Signal quality model | ✅ GOOD/BAD/UNCERTAIN/STALE/SIMULATED/MISSING | OPC UA compatible |
| UNS topic policy | ❌ Not defined | **Blocking MES integration** |
| Runtime event contract | ❌ Not defined | **Blocking MES integration** |
| `asset_role` field | ❌ Not in contract | Needed for MES mapping |
| `signal_type` beyond `measurement` | ❌ Only `measurement` used | Needed for status/event/alarm signals |
| Event envelope standard | ❌ Not defined | Blocking |

### 2.2 Gap Analysis vs SA Requirements

| SA Requirement | Current State | Gap |
|---------------|--------------|-----|
| Asset hierarchy: Plant→Area→Line→Work Cell→Equipment→Signal | Plant→Area→Asset→Signal | Missing `Line` and `Work Cell` levels |
| `asset_role`: functional_location / equipment / subsystem / component | Not present | Must add |
| `asset_classification`: mobility, maintainable, mes_mappable | Not present | Nice-to-have for MES readiness |
| Signal types: measurement, status, alarm, counter, calculated | Only `measurement` | Must expand vocabulary |
| Signal metadata: sampling_mode, quality_model, retention_policy | Not present | Nice-to-have for data governance |
| UNS topic policy: `{root}/{plant}/{area}/{asset}/{type}/{signal}` | Not defined | Critical gap |
| Runtime event contract: envelope + payload standards | Not defined | Critical gap |
| Validation rules | Not formalized | Must document |

### 2.3 Critique of SA Proposal

**Agree:**
1. `asset_role` with `functional_location | equipment | subsystem | component | logical_group` — correct taxonomy
2. `signal_type` vocabulary expansion — necessary for status/alarm signals
3. UNS topic structure `{root}/{plant}/{area}/{asset}/{type}/{signal_name}` — correct and follows ISA-95 / MIMOSA conventions
4. Event envelope with `schema_version`, `source_system`, `event_type`, `event_id`, `timestamp` — standard pattern
5. PlantOS must NOT model MES Work Orders — absolutely correct

**Disagree / concerns:**

| SA Proposal | PM Critique |
|-------------|-------------|
| Depth: Plant→Area→Line/Unit→Work Cell→Equipment→Signal | **Too prescriptive.** PlantOS should support flexible hierarchy depth (3-6 levels). Not every plant needs Line or Work Cell. WTP-DEMO-01 uses Process Unit → Equipment, not Line → Work Cell. Hierarchy should be configurable per plant, not enforced. |
| `asset_classification.mes_mappable` | **Leaky abstraction.** PlantOS shouldn't know it's "mappable to MES." This is MES's concern. Remove from PlantOS core contract. Replace with `external_context: {}` (opaque dict for external metadata). |
| `sampling_mode: event_driven \| periodic` | **Premature for MVP.** Only `periodic` exists today. `event_driven` requires OPC UA event subscription or MQTT retain — not supported yet. Flag as future. |
| `retention_policy` on signal | **Belongs in system config, not per-signal.** 120 signals × individual retention = management nightmare. Default policy + exception override only. |
| 6 documents output | **Too many for MVP.** Can consolidate: contract spec already covers assets/signals. Add UNS policy + Event contract as appendices. |
| `asset_type` vocabulary expansion with 40+ types | **Too granular.** The existing 20+ types cover current models. Add types on-demand per plant model, not pre-emptively. A type registry is better than a fixed enum. |

---

## 3. Proposed Asset Hierarchy Model

### 3.1 Flexible depth, not fixed levels

```text
Plant                    (required)
└── Area                 (required, at least 1)
    └── [Line | Process Unit | Utility System]  (optional)
        └── [Work Cell | Equipment Group]       (optional)
            └── Equipment                        (required for telemetry)
                └── [Subsystem]                  (optional, maintenance scope)
                    └── Signal                   (not an asset — separate entity)
```

**Rules:**
- Min depth: Plant → Area → Equipment (3 levels)
- Max recommended depth: 6 levels (warn above)
- Signal is never an asset — it's a first-class entity in signal registry
- `asset_role` determines the semantic level, not the depth

### 3.2 `asset_role` — mandatory for new contracts

```yaml
assets:
  - asset_id: LINE-A
    asset_role: functional_location
    asset_type: production_line

  - asset_id: ST-TQ-09
    asset_role: equipment
    asset_type: tool
    parent_asset_id: CELL-ASM-01
```

| `asset_role` | Meaning | Examples |
|-------------|---------|----------|
| `functional_location` | Grouping node for hierarchy/organization | Line, Cell, Station, System, Zone |
| `equipment` | Physical asset with telemetry | Pump, Motor, Compressor, Robot |
| `subsystem` | Maintainable component of equipment | Bearing assembly, Seal system |
| `component` | Small replaceable part | Only if lifecycle tracking needed |
| `logical_group` | Non-physical grouping for display | "Critical Path Assets", "Energy Monitors" |

### 3.3 Backward compatibility

Existing contracts without `asset_role` should default to:
```python
if asset_type in ("production_line", "work_cell", "equipment_group"):
    asset_role = "functional_location"
elif asset_type in ("compressor_train", "bearing_assembly", "seal_system", ...):
    asset_role = "subsystem"
else:
    asset_role = "equipment"
```

No breaking change. VF-DEMO and WTP-DEMO-01 continue to work.

---

## 4. Proposed Signal Registry Upgrade

### 4.1 Required fields (existing — no change)

```yaml
signal_id, asset_id, signal_name, display_name, signal_type,
data_type, engineering_unit, scale, offset, status
```

### 4.2 New required field

```yaml
signal_category: measurement  # measurement | status | alarm | counter | calculated | command
```

This is the `signal_type` vocabulary from the SA proposal, renamed to `signal_category` to avoid confusion with `data_type` (float/bool/int).

### 4.3 Optional fields (add but don't require)

```yaml
expected_interval_ms: 1000    # For gap detection
quality_model: simple         # simple | opcua_quality (default: simple)
external_refs:                # Opaque dict for external system references
  mes_signal_code: "SIG_TQ_09"
  sap_pm_point: "PM-TOOL-09"
```

### 4.4 What NOT to add

- `sampling_mode` — too early, requires event-driven ingestion
- `retention_policy` — belongs in system-level config
- `mes_mappable` flag — leaky abstraction, use `external_refs` instead

### 4.5 Clarification: `external_refs` is NOT integration source of truth

`external_refs` is a convenience field for PlantOS operators to attach opaque metadata (e.g., `sap_pm_point: "PM-TOOL-09"`). **It is not the MES mapping.** MES must maintain its own mapping contract that crosswalks PlantOS identifiers to MES line/workstation/equipment/operation IDs. PlantOS does not validate, consume, or depend on any external system's identifiers.

---

## 5. Proposed UNS Topic Policy

### 5.1 Topic structure

```text
{namespace}/{plant_id}/{area_id}/{asset_id}/{signal_category}/{signal_name}

Examples:
  plantos/vf-demo/compressor-area/comp01-core/measurement/speed
  plantos/wtp-demo-01/raw-water-intake/hsp-101/measurement/flow_rate
  plantos/vf-demo/compressor-area/comp01-motor/alarm/overcurrent
```

### 5.2 Namespace

```text
plantos   — Production namespace (owned by PlantOS)
```

### 5.3 Path encoding

| Segment | Source | Format |
|---------|--------|--------|
| `{plant_id}` | `plant.plant_id` | Lowercase, hyphens |
| `{area_id}` | `area.area_id` | Lowercase, hyphens |
| `{asset_id}` | `asset.asset_id` | Lowercase, hyphens |
| `{signal_category}` | `signal.signal_category` | Lowercase |
| `{signal_name}` | `signal.signal_name` | Lowercase, underscores |

### 5.4 Implementation — derived, not authored

**Modification #7:** UNS topics are **computed deterministically** from the PlantOS data model. They are never manually authored or stored in a database column. A signal's UNS topic is derived at runtime:

```python
def build_uns_topic(signal, asset, area, plant):
    return f"plantos/{plant.plant_id}/{area.area_id}/{asset.asset_id}/{signal.signal_category}/{signal.signal_name}"
```

Guarantee: given the same plant/area/asset/signal identifiers, the same UNS topic is ALWAYS produced. No configuration drift possible.

### 5.5 Crosswalk for MES

PlantOS exports identifier surface:
```json
{
  "uns_topic": "plantos/vf-demo/compressor-area/comp01-core/measurement/speed",
  "plant_id": "VF-DEMO",
  "area_id": "COMPRESSOR-AREA",
  "asset_id": "COMP01-CORE",
  "asset_code": "COMP01-CORE",
  "asset_type": "compressor",
  "asset_role": "equipment",
  "parent_asset_id": "COMP01",
  "signal_id": "COMP01-CORE.speed",
  "signal_name": "speed",
  "signal_category": "measurement",
  "data_type": "float",
  "engineering_unit": "RPM"
}
```

**Modification #4 — MES mapping contract is separate and owned by MES.** PlantOS does not store, validate, or consume MES work_order_id, operation_code, or product identifiers. MES maintains its own mapping file:

```yaml
# MES-owned: mes-plantos-signal-mapping.yaml
mappings:
  - plantos_signal_id: "COMP01-CORE.speed"
    mes_equipment_code: "EQ-COMP-01"
    mes_line_code: "LINE-A"
    mes_signal_code: "SIG_SPEED_01"
```

PlantOS exports the identifier surface. MES imports and maps. Neither system owns the other's identifiers.

---

## 6. Proposed Runtime Event Contract

### 6.1 Event types (MVP)

```yaml
SignalValueUpdated    # A signal value changed
AssetStatusChanged    # Asset lifecycle status changed
AlarmRaised           # Alarm condition triggered
AlarmCleared          # Alarm condition resolved
SignalQualityChanged  # Signal quality transition (GOOD→BAD etc.)
EdgeHeartbeatReceived # Edge agent reported health
```

### 6.2 Envelope (all events)

**Modification #1 — `correlation_id` added as optional field.**

```json
{
  "schema_version": "1.0",
  "source_system": "plantos_center",
  "event_id": "plantos-COMP01-CORE.speed-20260706T080000Z-a1b2c3",
  "correlation_id": "plantos-flush-edge-wtp-01-20260706T080000Z",
  "event_type": "SignalValueUpdated",
  "timestamp": "2026-07-06T08:00:00Z",
  "asset": {
    "plant_id": "VF-DEMO",
    "area_id": "COMPRESSOR-AREA",
    "asset_id": "COMP01-CORE",
    "asset_code": "COMP01-CORE",
    "asset_type": "compressor",
    "asset_role": "equipment"
  },
  "signal": {
    "signal_id": "COMP01-CORE.speed",
    "signal_name": "speed",
    "signal_category": "measurement",
    "data_type": "float",
    "engineering_unit": "RPM"
  },
  "uns_topic": "plantos/vf-demo/compressor-area/comp01-core/measurement/speed",
  "payload": {
    "value": 1480.5,
    "quality": "GOOD"
  }
}
```

`correlation_id`: Optional. Chains related events (e.g., a batch of signals from the same Edge Agent flush cycle). Set to `null` when no correlation exists. Format: freeform string, recommended `plantos-flush-{edge_hostname}-{ISO8601}`.

### 6.3 Event-specific required payload sections

**Modification #2 — Each event type has a defined payload schema:**

| Event Type | Required Payload Fields | Optional |
|-----------|------------------------|----------|
| `SignalValueUpdated` | `value` (number\|bool), `quality` (string) | — |
| `AssetStatusChanged` | `previous_status` (string), `new_status` (string) | `reason` (string) |
| `AlarmRaised` | `alarm_code` (string), `severity` (string), `description` (string) | `threshold_value`, `actual_value` |
| `AlarmCleared` | `alarm_code` (string) | `cleared_by` (string) |
| `SignalQualityChanged` | `previous_quality` (string), `new_quality` (string) | `reason` |
| `EdgeHeartbeatReceived` | `edge_hostname` (string), `signal_count` (int) | `version`, `ip_address` |

### 6.4 Idempotency

`event_id` is globally unique: `plantos-{signal_id}-{ISO8601}-{random6}`

MES deduplication: use `event_id` as idempotency key. No separate `idempotency_key` field needed — the `event_id` serves both purposes.

### 6.5 Delivery & QoS Policy

**Modification #5 — QoS by event type:**

| Event Type | MQTT QoS | Rationale |
|-----------|----------|-----------|
| `SignalValueUpdated` | QoS 0 | High frequency, loss-tolerant (next sample overwrites) |
| `AssetStatusChanged` | QoS 1 | Low frequency, state transition must be delivered |
| `AlarmRaised` | QoS 1 | Must not lose alarm events |
| `AlarmCleared` | QoS 1 | Must not lose alarm events |
| `SignalQualityChanged` | QoS 0 | Diagnostic, next quality update overwrites |
| `EdgeHeartbeatReceived` | QoS 0 | Periodic, next heartbeat overwrites |

Delivery:
- **Primary:** MQTT topic `plantos/events/{event_type}` (EMQX via `plantos-net`)
- **Fallback:** HTTP webhook (MES adapter subscribes to PlantOS events)
- **Format:** JSON, UTF-8, no envelope compression for MVP

### 6.6 Future: Batch Envelope (documentation only — not implemented in Phase 9D)

**Modification #6 — Documented for future reference. Not implemented now.**

```json
{
  "schema_version": "1.0",
  "source_system": "plantos_center",
  "event_id": "plantos-batch-20260706T080000Z-d4e5f6",
  "event_type": "BatchSignalValuesUpdated",
  "timestamp": "2026-07-06T08:00:00Z",
  "correlation_id": "plantos-flush-edge-wtp-01-20260706T080000Z",
  "batch_size": 92,
  "events": []
}
```

When signal volume exceeds ~200 events/s, batch mode should be reconsidered.

---

## 7. Validation Rules

### 7.1 Asset validation

```yaml
- asset_id unique across plant
- parent_asset_id references existing asset or null
- No circular references in hierarchy
- Max depth warning at >6 levels
- asset_role required for new contracts
- asset_role must be in controlled vocabulary
- equipment role assets should normally have associated signals
```

### 7.2 Signal validation

```yaml
- signal_id unique across plant
- signal_id matches pattern {asset_id}.{signal_name}
- asset_id references existing asset
- signal_category in controlled vocabulary
- engineering_unit recognized (warning if unknown)
- signal_name valid snake_case
```

### 7.3 Runtime event validation

**Modification #8 — Validation rules with concrete examples:**

```yaml
Structural:
  - event_id: required, globally unique, format plantos-{id}-{ISO8601}-{random6}
  - timestamp: required, ISO8601 with timezone (Z or +HH:MM)
  - event_type: required, must be in controlled vocabulary
  - source_system: required, must equal "plantos_center"
  - correlation_id: optional; if present, non-empty string

Referential:
  - asset.asset_id: must exist in PlantOS asset registry
  - signal.signal_id: must exist for SignalValueUpdated, SignalQualityChanged
  - uns_topic: must match derived topic from asset/signal identifiers (validated at publish time, not in consumer)

Payload (event-type specific):
  - SignalValueUpdated: payload.value must be present; payload.quality in [GOOD, BAD, UNCERTAIN, STALE, SIMULATED, MISSING]
  - AlarmRaised: payload.alarm_code required; payload.severity in [critical, high, medium, low]
  - AlarmCleared: payload.alarm_code required
  - AssetStatusChanged: payload.previous_status and payload.new_status required
  - SignalQualityChanged: payload.previous_quality and payload.new_quality required
  - EdgeHeartbeatReceived: payload.edge_hostname required

Validation example — VALID:
  event_id: "plantos-COMP01-CORE.speed-20260706T080000Z-a1b2c3"  ✓
  timestamp: "2026-07-06T08:00:00Z"                             ✓
  payload: { "value": 1480.5, "quality": "GOOD" }               ✓

Validation example — INVALID:
  event_id: "evt-123"                    ✗ (wrong format)
  timestamp: "2026-07-06 08:00:00"        ✗ (no timezone)
  payload: { "value": "1480.5" }          ✗ (value is string, should be number)
  payload: {}                             ✗ (missing quality for SignalValueUpdated)
```

---

## 8. Required File Changes

### 8.1 Documentation

| File | Action | Priority |
|------|--------|----------|
| `docs/plantos-integration-contract-spec.md` | Add §asset_role, §signal_category, §UNS topic, §event contract | P0 |
| `docs/20-data-model.md` | Update asset/signal entities with new fields | P0 |
| `docs/adr/ADR-0007-plantos-mes-integration-boundary.md` | New — SA decision record | P0 |
| `docs/22-uns-topic-policy.md` | New — UNS namespace governance | P1 |
| `docs/23-runtime-event-contract.md` | New — event envelope + payload standards | P1 |
| `docs/24-signal-registry-spec.md` | New — signal metadata specification | P2 |

### 8.2 Contract/Schema

| File | Action | Priority |
|------|--------|----------|
| `schemas/plantos-integration-contract.schema.json` | Add `asset_role`, `signal_category` to JSON Schema | P0 |
| `examples/vf-plantos-contract.yaml` | Update with new fields | P1 |
| `examples/contracts/wtp-demo-01.contract.yaml` | Update with new fields | P1 |
| `examples/plantos-runtime-event-examples.json` | New — example event payloads | P2 |

### 8.3 Backend Code

| File | Action | Priority |
|------|--------|----------|
| `backend/app/modules/contracts/` | Update validator to check new fields | P0 |
| `backend/migrations/versions/005_asset_signal_upgrade.py` | Add columns: `asset_role`, `signal_category`, `external_refs` | P0 |
| `backend/app/modules/assets/router.py` | Expose `asset_role` in API response | P1 |
| `backend/app/modules/signals/router.py` | Expose `signal_category` in API response | P1 |
| `backend/app/modules/events/router.py` | New — event publishing endpoint | P1 |

### 8.4 Frontend Code

| File | Action | Priority |
|------|--------|----------|
| Asset detail page | Show `asset_role` badge | P2 |
| Signal table | Show `signal_category` column | P2 |
| System page | Show UNS topic policy status | P2 |

---

## 9. Implementation Phases

### Phase 9A — Contract & Schema Upgrade (3-4h)
```
1. Add asset_role, signal_category to contract spec + JSON schema
2. Add validation rules in contract validator
3. Update existing VF-DEMO + WTP-DEMO-01 contracts with new fields (backward compat)
4. Create ADR-0007
```
**Acceptance:** Existing contracts validate successfully. New fields parse correctly.

### Phase 9B — DB Migration + API (2-3h)
```
1. Migration 005: add asset_role, signal_category columns
2. Backfill existing data from asset_type → asset_role mapping
3. Expose new fields in GET /assets, GET /signals APIs
4. Update seed scripts
```
**Acceptance:** API returns new fields. Existing frontend unaffected.

### Phase 9C — UNS Topic Policy (1-2h)
```
1. Define UNS topic derivation function
2. Add uns_topic to signal API response
3. Document UNS topic policy
```
**Acceptance:** Every signal has a deterministic UNS topic.

### Phase 9D — Runtime Event Contract (2-3h)
```
1. Define event envelope + payload schemas
2. Create event publishing service (MQTT topic)
3. Wire up to existing measurement ingestion pipeline
4. Create example event payloads
```
**Acceptance:** Measurement ingestion triggers `SignalValueUpdated` events on MQTT.

### Phase 9E — MES Readiness Validation (1-2h)
```
1. Crosswalk export: run script to export all asset/signal identifiers
2. Validate against SA acceptance criteria
3. Create MES integration readiness report
```
**Acceptance:** External system can consume all identifiers for mapping.

---

## 10. Risks / Open Questions

### 10.1 Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| MES team demands WO context in PlantOS events | Scope creep into PlantOS core | Reject per ADR; redirect to MES adapter layer |
| Signal volume grows beyond MQTT capacity | Event delivery bottleneck | Add Kafka connector in future phase; MQTT sufficient for current 92 signals @ 1-30s |
| `asset_role` semantic drift between plants | "Line" means different things in different industries | Document per-plant guidelines; validate at contract import time |
| UNS topic namespace collision with other systems | Multiple systems claiming same namespace | PlantOS claims `plantos/` root; documented in UNS policy |

### 10.2 Questions for SA (to resolve before Phase 9D)

1. **Event delivery guaranteed?** Should events be at-least-once (MQTT QoS 1) or best-effort (QoS 0)? Recommendation: QoS 1 for alarm events, QoS 0 for measurement events.

2. **Event history?** Does MES need replay capability for missed events, or is current-value-only acceptable? Recommendation: Events are point-in-time; replay from historian if MES needs history.

3. **Batch vs single?** Should we emit one MQTT message per signal per sample, or batch N signals per message? Recommendation: Per-signal for simplicity; batch mode in future if throughput demands it.

---

## 11. Acceptance Criteria Mapping

| SA Criterion | Phase | Status |
|-------------|-------|--------|
| Asset hierarchy supports Plant→Area→Line→Equipment→Signal | 9A | ✅ In plan |
| Workstation can be `asset_role=functional_location` | 9A | ✅ In plan |
| Signal registry is first-class | Existing | ✅ Already |
| Runtime events include stable asset_id + signal_id | 9D | ✅ In plan |
| Payload does NOT require work_order_id | By design | ✅ Per ADR |
| UNS topic is asset/signal-centric | 9C | ✅ In plan |
| Payload includes enough identifiers for MES mapping | 9C | ✅ In plan |
| Protocol bindings remain extensions | Existing | ✅ Already |
| Validation rules prevent invalid hierarchy | 9A | ✅ In plan |
| Example contract consumable by MES adapter | 9E | ✅ In plan |

---

## 12. Answers to 4 Open Questions

### Q1: PlantOS đã có UNS topic namespace chuẩn chưa?

**Chưa.** Hiện tại PlantOS chưa định nghĩa UNS topic policy. Các signal được identify qua `signal_id` (vd: `COMP01-CORE.speed`) nhưng không có namespace, topic path, hay convention cho external consumption.

**Đề xuất:** Phase 9C — định nghĩa UNS topic structure:
```
plantos/{plant_id_lower}/{area_id_lower}/{asset_id_lower}/{signal_category}/{signal_name}
```
Namespace root: `plantos/` (PlantOS sở hữu). Topic được **derive** từ data model, không lưu riêng. Mỗi signal có đúng 1 topic, deterministic.

**Timeline:** Có trong 1-2h sau khi Phase 9A-B hoàn tất.

### Q2: PlantOS có hỗ trợ idempotency_key không?

**Có — thông qua `event_id`.** Mỗi runtime event có `event_id` format:
```
plantos-{signal_id}-{ISO8601_timestamp}-{random6}
```
`event_id` đóng vai trò vừa là unique identifier vừa là idempotency key. MES deduplicate bằng `event_id`. Không cần field riêng.

**Timeline:** Sẽ có trong Phase 9D (Runtime Event Contract).

### Q3: Ai owns canonical.signal master data? MES sync từ PlantOS hay nhập tay?

**PlantOS owns canonical signal master data.** Lý do:
- PlantOS là nguồn duy nhất của asset hierarchy, signal registry, và protocol bindings (OPC UA, Modbus)
- Signal được khai báo trong PlantOS Integration Contract → import vào Center → seed vào PostgreSQL
- MES không có OPC UA binding, không biết protocol-level detail
- Flow: `Contract YAML → PlantOS Center (PG) → API export → MES import`

**Integration pattern:**
```
1. PlantOS exports signal registry as JSON/CSV (Phase 9E)
2. MES imports, maps to internal equipment/signal model
3. On PlantOS contract update: MES pulls diff via API
4. MES never creates signals; PlantOS never creates work orders
```

### Q4: PlantOS event rate dự kiến?

**Current (WTP-DEMO-01):**
- 92 signals × every 30s = ~3 events/s
- Peak (WTP + VF + future plant): ~200 signals × every 10s = 20 events/s
- Burst (store-and-forward catch-up): up to 500 events in 1 batch

**For MES dedup strategy:**
- Event ID format: `plantos-{signal_id}-{ISO8601}-{random6}`
- Dedup window: MES should retain seen `event_id` set for 1h (configurable)
- At 20 events/s × 3600s = 72K IDs in dedup cache — trivial for Redis/PostgreSQL
- No separate `idempotency_key` needed — `event_id` is sufficient

**Recommendation:** MES implements dedup by `event_id` with 1h sliding window. PlantOS guarantees `event_id` uniqueness.

---

## 13. Summary

| Deliverable | Phase | Effort |
|-------------|-------|--------|
| Contract spec update (asset_role, signal_category) | 9A | 2h |
| JSON schema update + validation rules | 9A | 1h |
| ADR-0007 | 9A | 1h |
| DB migration + API update | 9B | 3h |
| UNS topic policy | 9C | 2h |
| Runtime event contract + MQTT publishing | 9D | 3h |
| MES readiness report + crosswalk export | 9E | 2h |
| **Total** | | **~14h** |

**Next step:** SA review of this plan → approve → begin Phase 9A.
