# PlantOS MES Integration Readiness Report

> **Version:** 1.0 | **Date:** 2026-07-06  
> **For:** SA + MES PM Review  
> **Status:** Phases 9A, 9B, 9C complete

---

## 1. Summary

PlantOS has completed the foundation phases for MES integration. The semantic core (asset hierarchy, signal registry, UNS topic policy) is upgraded and ready for MES to consume.

## 2. Completed Work

| Phase | Status | Deliverables |
|-------|--------|-------------|
| 9A — Contract & Schema Upgrade | ✅ | `asset_role`, `signal_category` in contract spec + JSON Schema v2.0; ADR-0007 |
| 9B — DB Migration + API | ✅ | Migration 005 applied; API returns new fields |
| 9C — UNS Topic Policy | ✅ | `plantos/{plant}/{area}/{asset}/{category}/{signal_name}` derivation implemented |
| 9D — Runtime Event Contract | ⏸ Deferred | Contract designed, implementation pending SA approval |
| 9E — This Report | ✅ | You are reading it |

## 3. Asset Hierarchy — MES-Ready

PlantOS now supports flexible asset hierarchy with semantic roles:

```
VF-DEMO (Plant)
└── COMPRESSOR-AREA (Area)
    └── COMP01 (asset_role=equipment, asset_type=compressor_train)
        ├── COMP01-MOTOR (asset_role=equipment)
        ├── COMP01-CORE (asset_role=equipment)
        └── COMP01-BEARINGS (asset_role=subsystem)
```

**All 55 existing assets have been backfilled with `asset_role`**:
- `functional_location`: 0 (none in current models; available for future)
- `equipment`: 53
- `subsystem`: 2

## 4. Signal Registry — MES-Ready

**120 signals with `signal_category`:**

| Category | Count | Example |
|----------|-------|---------|
| `measurement` | 118 | `COMP01-CORE.speed`, `HSP-101.flow_rate` |
| `status` | 2 | `TRANSFER-OUTLET-QUALITY-STATION-101.outlet_compliance_status` |
| `alarm` | 0 | Available for future |
| `counter` | 0 | Available for future |
| `calculated` | 0 | Available for future |

## 5. UNS Topic Policy

Every signal has a deterministic UNS topic:

```
plantos/{plant_id_lower}/{area_id_lower}/{asset_id_lower}/{signal_category}/{signal_name}

Examples:
  plantos/vf-demo/compressor-area/comp01-core/measurement/speed
  plantos/wtp-demo-01/raw-water-intake/hsp-101/measurement/flow_rate
```

**Guarantee:** Same identifiers → same topic. Always. Computed at runtime, never stored.

## 6. Identifier Surface for MES Crosswalk

PlantOS exports the following identifiers for MES to map:

| Field | Example | MES Use |
|-------|---------|---------|
| `plant_id` | `VF-DEMO` | Map to MES site/facility |
| `area_id` | `COMPRESSOR-AREA` | Map to MES area/zone |
| `asset_id` | `COMP01-CORE` | Map to MES equipment |
| `asset_type` | `compressor` | Equipment classification |
| `asset_role` | `equipment` | Semantic role in hierarchy |
| `signal_id` | `COMP01-CORE.speed` | Map to MES signal |
| `signal_name` | `speed` | Signal short name |
| `signal_category` | `measurement` | Signal type context |
| `engineering_unit` | `RPM` | Unit for display/validation |
| `uns_topic` | `plantos/vf-demo/...` | MQTT subscription target |

## 7. What MES Should Prepare

Based on the PlantOS identifier surface, MES team should:

1. **Draft mapping contract** — crosswalk PlantOS `plant_id`/`area_id`/`asset_id`/`signal_id` to MES internal line/workstation/equipment/signal codes
2. **Prepare MQTT subscription** — subscribe to `plantos/events/SignalValueUpdated` for real-time data
3. **Implement dedup** — by `event_id` with 1h sliding window
4. **Review runtime event contract** — validate that `SignalValueUpdated` payload meets MES needs

## 8. Pending: Phase 9D (Runtime Events)

The runtime event contract is fully designed (see `phase9-mes-integration-plan.md` §6) but implementation is deferred until:

1. SA approves the updated event contract (with all 8 modifications)
2. MES confirms the event payload schema is sufficient
3. MES adapter team is ready to consume events

## 9. Validation

```
✓ asset_role present for all 55 assets
✓ signal_category present for all 120 signals
✓ UNS topic derivable for all 120 signals
✓ No MES identifiers in PlantOS core data model
✓ ADR-0007 documents the integration boundary
✓ Contract spec updated to v2.0
✓ JSON Schema updated to v2.0
```

---

**Prepared by:** PlantOS PM-Designer  
**Next step:** SA + MES PM review → approve → begin MES C0-C3 preparation
