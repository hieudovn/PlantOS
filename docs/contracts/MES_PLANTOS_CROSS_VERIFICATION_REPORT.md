# MES PlantOS Cross-Project Verification Report

> **Date:** 2026-07-06  
> **Verified by:** PlantOS PM-Designer  
> **Source (MES):** `MES_PLANTOS_FINAL_COMPLETION_REPORT.md`  
> **Source (PlantOS):** `docs/contracts/PLANTOS_RUNTIME_EVENT_CONTRACT.md` v2.0-final  
> **Status:** CONDITIONAL PASS — 1 P0 fix required before production

---

## 1. Verification Scope

Cross-referenced the MES Final Completion Report and MES codebase against the PlantOS Phase 9D final contract bundle:

| PlantOS Artefact | Version |
|------------------|---------|
| `PLANTOS_RUNTIME_EVENT_CONTRACT.md` | 2.0-final, SA Approved |
| `PLANTOS_RUNTIME_TOPIC_POLICY.md` | 1.0, Final |
| `plantos-runtime-event-examples.json` | 1.0 |
| `PLANTOS_ASSET_SIGNAL_EXPORT_SAMPLE.json` | 2.0 |
| `ADR-0007-plantos-mes-integration-boundary.md` | ACCEPTED |

---

## 2. Architecture Compliance — ✅ PASS (7/7)

| # | Principle | PlantOS Source | MES Implementation | Status |
|---|-----------|---------------|-------------------|--------|
| 1 | PlantOS publishes. MES interprets. | Contract preamble | Adapter is consumer-only; no write-back | ✅ |
| 2 | PlantOS owns asset/signal/telemetry master | ADR-0007 §D2 | `canonical.signal` is reference copy | ✅ |
| 3 | PlantOS does NOT send WO/MO/Operation | Contract §8 | PlantOS owns exclusion; MES doesn't filter | ✅ |
| 4 | MES enriches production context internally | Contract preamble | `PlantOSContextResolver` 4-step chain | ✅ |
| 5 | No CDM merge | ADR-0007 §D5 | Separate CDMs, identity mapping join | ✅ |
| 6 | Identity mapping, not hardcoding | ADR-0007 §D8 | `canonical.identity.map` with `source_system=plantos` | ✅ |
| 7 | Raw alarm ≠ operator-confirmed fault | ADR-0007 §D4 | `alarm_raised` ≠ `machine_down` | ✅ |

---

## 3. Event Type Mapping — ✅ PASS (6/6)

Verified across 3 mapping surfaces (adapter, model, JSON config):

| PlantOS Event | MES `event_type` | Canonical Event | Adapter | Model | JSON |
|--------------|-----------------|-----------------|---------|-------|------|
| `SignalValueUpdated` | `measurement_received` | `ProcessMeasurementRecorded` | ✅ | ✅ | ✅ |
| `AssetStatusChanged` | `equipment_status_changed` | `EquipmentStatusChanged` | ✅ | ✅ | ✅ |
| `AlarmRaised` | `alarm_raised` | `AlarmRaised` | ✅ | ✅ | ✅ |
| `AlarmCleared` | `alarm_cleared` | `AlarmCleared` | ✅ | ✅ | ✅ |
| `SignalQualityChanged` | `signal_quality_changed` | `SignalQualityChanged` | ✅ | ✅ | ✅ |
| `EdgeHeartbeatReceived` | `edge_heartbeat` | `EdgeHeartbeatReceived` | ✅ | ✅ | ✅ |

> `CounterUpdated` and `DataGapDetected` exist in MES catalog as future-proofing — not in PlantOS 9D contract. Acceptable.

---

## 4. Topic Routing — ⚠️ CONDITIONAL PASS

### Bridge Subscriptions (verified in `uns_config.yaml`)

| Pattern | Action | Covers | Status |
|---------|--------|--------|--------|
| `plantos/+/+/+/+/+` | `process_plantos_event` | SignalValueUpdated | ✅ Correct |
| `plantos/events/+` | `process_plantos_event` | AssetStatusChanged, AlarmRaised, AlarmCleared, SignalQualityChanged, EdgeHeartbeatReceived | ✅ Correct |

Both patterns route to the same handler — coverage is complete.

### Documentation Discrepancy

The MES report §5 incorrectly places `SignalQualityChanged` in the signal UNS row instead of the event topic row. The bridge receives it correctly via `plantos/events/+` — functionally OK, but documentation is misleading.

| Source | SignalQualityChanged route |
|--------|---------------------------|
| PlantOS Contract §1 | `plantos/events/SignalQualityChanged` ✅ |
| MES Report §5 | `plantos/{plant}/{area}/{asset}/{category}/{signal}` ❌ |
| MES `uns_config.yaml` comment | "SignalValueUpdated / SignalQualityChanged via UNS topic" ❌ |

---

## 5. event_id Format — 🔴 CRITICAL MISMATCH

### PlantOS Contract §5 (Source of Truth)

```
Format:  plantos-{entity_id_lower}-{YYYYMMDDTHHMMSSZ}-{random6}
Example: plantos-hsp-101.flow_rate-20260706t120000z-a1b2c3
Regex:   ^plantos-[a-z0-9_.-]+-\d{8}t\d{6}z-[a-f0-9]{6}$

Rules:
  - Timestamp uses lowercase 't' and 'z' (e.g., 20260706t120000z)
```

### MES Adapter Regex (`plantos_adapter.py:18`)

```python
_EVENT_ID_RE = re.compile(
    r"^plantos-[a-z0-9_.-]+-\d{8}T\d{6}Z-[a-f0-9]{6}$"
)
```

### Mismatch Analysis

| Component | PlantOS Contract | MES Adapter Regex | Match? |
|-----------|-----------------|-------------------|--------|
| Prefix | `plantos-` | `plantos-` | ✅ |
| entity_id | `[a-z0-9_.-]+` | `[a-z0-9_.-]+` | ✅ |
| Timestamp separator | `t` (lowercase) | `T` (uppercase) | 🔴 NO |
| Timestamp suffix | `z` (lowercase) | `Z` (uppercase) | 🔴 NO |
| random6 | `[a-f0-9]{6}` | `[a-f0-9]{6}` | ✅ |

### Impact

**All PlantOS events will be REJECTED at Step 1 validation** (`invalid_event_id_format`). The regex is compiled without `re.IGNORECASE` and uses uppercase literal characters. PlantOS emits lowercase per the contract.

### MES Test Script Events

The test script uses lowercase `t`/`z`:
```
event_id: plantos-comp01-core.speed-20260706t080000z-a1b2c3
```

This means the test events would also fail against the adapter regex. The 8/8 test pass claim may be inaccurate if tested end-to-end through the adapter.

---

## 6. QoS Policy — ⚠️ MINOR DISCREPANCY

| Event Type | PlantOS Contract §6 | MES Report §5 | Match? |
|-----------|-------------------|---------------|--------|
| SignalValueUpdated | 0 | 0 | ✅ |
| AssetStatusChanged | 1 | 1 | ✅ |
| AlarmRaised | 1 | 1 | ✅ |
| AlarmCleared | 1 | 1 | ✅ |
| SignalQualityChanged | **1** | **0** (configurable 1) | 🟡 |
| EdgeHeartbeatReceived | 0 | 0 | ✅ |

---

## 7. Identity Mapping — ✅ PASS

- `asset.asset_id` used as primary mapping key → `canonical.identity.map` → `mes_code`
- `signal.signal_id` extracted but not used for identity resolution (correct — per contract, signal_id is secondary)
- `asset: null` for EdgeHeartbeat correctly skips identity resolution
- `external_event_id` unique constraint enforces idempotency

---

## 8. Payload Fields — ✅ PASS

MES adapter stores the entire PlantOS envelope in `payload_json`. No field filtering on MES side. This is architecturally correct — PlantOS owns the exclusion per contract §8. Verified all 7 test examples have zero WO/MO/Operation fields.

---

## 9. Test Coverage (8/8) — ⚠️ CONDITIONAL PASS

All 8 test cases structurally match PlantOS contract:

| TC | Event | Expect | Structure | event_id lowercase? |
|----|-------|--------|-----------|-------------------|
| 1 | SignalValueUpdated | created | ✅ | ✅ t/z lowercase |
| 2 | SignalValueUpdated | created | ✅ | ✅ t/z lowercase |
| 3 | Duplicate | duplicate | ✅ | ✅ t/z lowercase |
| 4 | Unmapped | waiting_for_mapping | ✅ | ✅ t/z lowercase |
| 5 | AlarmRaised | created | ✅ | ✅ t/z lowercase |
| 6 | AlarmCleared | created | ✅ | ✅ t/z lowercase |
| 7 | SignalQualityChanged | created | ✅ | ✅ t/z lowercase |
| 8 | EdgeHeartbeatReceived | created | ✅ | ✅ t/z lowercase |

> ⚠️ Test events use lowercase t/z but adapter regex expects uppercase T/Z. End-to-end test may not pass through full adapter validation path unless the regex was temporarily relaxed during testing.

---

## 10. Summary

| Category | Result |
|----------|--------|
| Architecture compliance (7 principles) | ✅ PASS |
| Event type mapping (6 types, 3 surfaces) | ✅ PASS |
| Identity resolution | ✅ PASS |
| Idempotency | ✅ PASS |
| Alarm lifecycle | ✅ PASS |
| Bridge subscription coverage | ✅ PASS |
| Test case structure (8/8) | ✅ PASS |
| **event_id regex** | 🔴 **FAIL — P0 fix required** |
| Topic routing documentation | 🟡 P1 — doc correction needed |
| QoS documentation | 🟡 P1 — doc correction needed |

### Final Verdict: CONDITIONAL PASS

**Production blocked** until P0 fix applied. P1 documentation corrections recommended but not blocking.

Detailed fix instructions: `docs/contracts/MES_PLANTOS_FIX_PATCH.md`

---

> **This report is part of the PlantOS Phase 9D final artefact bundle.**  
> Share with MES PM for C8 remediation before production go-live.
