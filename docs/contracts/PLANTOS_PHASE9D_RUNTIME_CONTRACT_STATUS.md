# PlantOS Phase 9D — Runtime Contract Status

> **Date:** 2026-07-06  
> **Prepared by:** PlantOS PM-Designer  
> **For:** SA + MES PM

---

## Status Summary

```
PlantOS Phase 9A–9C: COMPLETED ✅
PlantOS Phase 9D:     SA APPROVED ✅ — Implementation authorized
MES C8/C9/C10:        UNBLOCKED — MES may proceed with PlantOSAdapter
```

---

## Completed

| Phase | Deliverable | Status |
|-------|------------|--------|
| 9A | Contract spec v2.0 (`asset_role`, `signal_category`) | ✅ Deployed |
| 9A | JSON Schema v2.0 | ✅ Deployed |
| 9A | ADR-0007 (integration boundary) | ✅ Accepted |
| 9B | Migration 005 (asset_role, signal_category, external_refs) | ✅ Applied |
| 9B | API updated (55 assets, 120 signals with new fields) | ✅ Deployed |
| 9C | UNS topic derivation (`plantos/{plant}/{area}/{asset}/{category}/{signal}`) | ✅ Implemented |
| 9C | `build_uns_topic()` function | ✅ Deployed |

## SA Approved — Phase 9D Final Artefacts

| Artifact | File | Status |
|----------|------|--------|
| Runtime event contract | `docs/contracts/PLANTOS_RUNTIME_EVENT_CONTRACT.md` | ✅ SA Approved |
| Runtime topic policy | `docs/contracts/PLANTOS_RUNTIME_TOPIC_POLICY.md` | ✅ SA Approved |
| Asset/signal export sample | `examples/PLANTOS_ASSET_SIGNAL_EXPORT_SAMPLE.json` | ✅ SA Approved |
| Runtime event examples | `examples/plantos-runtime-event-examples.json` | ✅ SA Approved |

## MES Artifact Dependencies

| MES Phase | Requires from PlantOS | Status |
|-----------|----------------------|--------|
| C0-C3 (model prep) | Asset/signal export + UNS topic policy | ✅ Available |
| C5-C6 (mapping draft) | Runtime event contract + examples | ✅ Available |
| C8 (runtime adapter) | Final approved event contract | ✅ UNBLOCKED — SA approved 2026-07-06 |
| C9 (integration test) | Live event stream | 🔜 Pending — PlantOS implementation |
| C10 (production go-live) | Stable event stream + monitoring | 🔜 Pending — after C9 |

## Key Decisions Embedded in Contract

| Decision | Resolution |
|----------|-----------|
| Topic model | Hybrid — signal UNS for telemetry, `plantos/events/{type}` for system events |
| event_id format | `plantos-{entity}-{ISO8601}-{random6}` |
| Idempotency | event_id doubles as idempotency key |
| Alarm lifecycle | correlation_id pairs AlarmRaised + AlarmCleared |
| QoS | 0 for telemetry/heartbeat, 1 for alarms/status/quality |
| MES context | Zero WO/MO/Operation fields in PlantOS payload |

## Bundle Verification

```
✅ event_id format finalized: plantos-{entity_id_lower}-{YYYYMMDDTHHMMSSZ}-{random6}, retry uses same event_id
✅ Identity mapping: asset.asset_id primary, signal.signal_id primary, asset.asset_code secondary
✅ Topic model finalized: hybrid — signal UNS for SignalValueUpdated, plantos/events/{event_type} for system events
✅ uns_topic semantics: signal UNS topic for SignalValueUpdated, event topic for system events
✅ No MES production context fields in any payload
```

## Readiness Checklist

```
✅ Runtime topic model finalized
✅ Event envelope finalized
✅ Event-specific required fields finalized
✅ event_id/idempotency rule finalized
✅ QoS policy finalized
✅ Alarm lifecycle finalized
✅ Asset/signal export sample provided
✅ Runtime examples provided
✅ No WO/MO/Operation fields in any example
✅ SA approved
```

---

## PM DECISION: Ready for implementation

**CAN MES START C8?** Yes — unblocked. SA approved Phase 9D contract on 2026-07-06.

**NEXT ACTIONS:**
1. PlantOS implements runtime event publishing based on final contract
2. MES proceeds with C8 PlantOSAdapter implementation
3. MES finalizes C10 after PlantOS event stream is live

---

## Cross-Project Verification (2026-07-06)

MES PlantOSAdapter implementation was verified against PlantOS Phase 9D final contract.
Full report: `docs/contracts/MES_PLANTOS_CROSS_VERIFICATION_REPORT.md`

### Verification Summary

| Area | Result |
|------|--------|
| Architecture principles (7/7) | ✅ PASS |
| Event type mapping (6/6) | ✅ PASS |
| Identity resolution | ✅ PASS |
| Idempotency via external_event_id | ✅ PASS |
| Alarm lifecycle via correlation_id | ✅ PASS |
| Bridge topic subscriptions | ✅ PASS |
| Test cases (8/8) | ✅ PASS — structurally valid |

### Cross-Project Issues Found

| # | Priority | Issue | Owner |
|---|----------|-------|-------|
| 1 | 🔴 P0 | **event_id regex T/Z case**: MES adapter expects uppercase `T`/`Z` in regex (`\d{8}T\d{6}Z`), PlantOS emits lowercase `t`/`z` per contract §5 (`20260706t120000z`). All events will be rejected at validation. Fix: change regex to `\d{8}[tT]\d{6}[zZ]` or `\d{8}t\d{6}z`. | MES PM |
| 2 | 🟡 P1 | **SignalQualityChanged topic misdocumented** in MES report: placed in signal UNS row. PlantOS contract §1 routes it to `plantos/events/SignalQualityChanged`. Bridge subscribes to both patterns — functionally OK, doc only. | MES PM |
| 3 | 🟡 P1 | **SignalQualityChanged QoS misstated** in MES report: says QoS 0. PlantOS contract §6 specifies QoS 1. | MES PM |

### MES Fix Patch

See `docs/contracts/MES_PLANTOS_FIX_PATCH.md` for exact code changes MES PM must apply.

---

> **This bundle is the source of truth for MES PlantOSAdapter implementation.**
> Any later change to runtime topic, event envelope, event_id, identity key, alarm lifecycle, or QoS policy must be versioned and reviewed by SA + MES PM before implementation impact is accepted.
