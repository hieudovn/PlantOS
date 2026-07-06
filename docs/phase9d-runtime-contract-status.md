# PlantOS Phase 9D — Runtime Contract Status

> **Date:** 2026-07-06  
> **Prepared by:** PlantOS PM-Designer  
> **For:** SA + MES PM Review

---

## Status Summary

```
PlantOS Phase 9A–9C: COMPLETED ✅
PlantOS Phase 9D:     DESIGN FINALIZED — pending SA approval
MES C8/C9/C10:        BLOCKED until Phase 9D approved
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

## Pending SA Approval

| Artifact | File | Status |
|----------|------|--------|
| Runtime event contract (final) | `docs/contracts/PLANTOS_RUNTIME_EVENT_CONTRACT_DRAFT.md` | 📋 For review |
| Runtime topic policy | `docs/contracts/PLANTOS_RUNTIME_TOPIC_POLICY.md` | 📋 For review |
| Asset/signal export sample | `examples/PLANTOS_ASSET_SIGNAL_EXPORT_SAMPLE.json` | 📋 For review |
| Runtime event examples | `examples/plantos-runtime-event-examples.json` | 📋 For review |

## MES Artifact Dependencies

| MES Phase | Requires from PlantOS | Status |
|-----------|----------------------|--------|
| C0-C3 (model prep) | Asset/signal export + UNS topic policy | ✅ Available |
| C5-C6 (mapping draft) | Runtime event contract + examples | 📋 Available for draft review |
| C8 (runtime adapter) | Final approved event contract | 🔒 Blocked — waiting SA approval |
| C9 (integration test) | Live event stream | 🔒 Blocked — waiting C8 |
| C10 (production go-live) | Stable event stream + monitoring | 🔒 Blocked — waiting C9 |

## Key Decisions Embedded in Contract

| Decision | Resolution |
|----------|-----------|
| Topic model | Hybrid — signal UNS for telemetry, `plantos/events/{type}` for system events |
| event_id format | `plantos-{entity}-{ISO8601}-{random6}` |
| Idempotency | event_id doubles as idempotency key |
| Alarm lifecycle | correlation_id pairs AlarmRaised + AlarmCleared |
| QoS | 0 for telemetry/heartbeat, 1 for alarms/status/quality |
| MES context | Zero WO/MO/Operation fields in PlantOS payload |

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
```

---

## PM DECISION: Ready for SA review

**CAN MES START C8?** No — blocked until SA approves Phase 9D contract.

**BLOCKERS:**
1. SA must review and approve runtime event contract
2. SA must confirm topic model (hybrid)
3. SA must confirm alarm lifecycle rules

**NEXT ACTIONS:**
1. SA reviews 4 artifacts
2. SA approves → PlantOS Phase 9D implementation begins
3. MES C8 unblocked after PlantOS event stream is live
