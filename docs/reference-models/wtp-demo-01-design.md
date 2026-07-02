# WTP-DEMO-01 — Water Treatment Plant Reference Model: Design Document

> **Status:** Draft | **Phase:** 8A | **Date:** 2026-07-02
> **Contract:** `examples/contracts/wtp-demo-01.contract.yaml`
> **Related:** `docs/prompts/phase8a-vf-wtp-simulator-pm-prompt.md` (VF track)

---

## 1. Objective

WTP-DEMO-01 is the **first PlantOS industry reference model**. It proves that PlantOS can govern, import, simulate, monitor, and trace an industrial production process end-to-end using the Integration Contract v2 pipeline:

```
Contract YAML → Validate → Preview → Apply → Asset/Signal Registry → Simulator → Ingestion → Historian → Visualization
```

The model covers a realistic municipal water treatment plant with five monitoring layers and eight abnormal scenarios.

---

## 2. Process Overview

```
Raw Water Intake (river/reservoir)
  │ raw_turbidity 10-120 NTU, raw_pH 6.8-7.5
  ▼
Screening / Raw Water Pumping
  │ screen DP, pump flow, motor current/vibration
  ▼
Chemical Dosing (coagulant + pH correction)
  │ coagulant dose proportional to raw turbidity
  ▼
Flash Mixing → Flocculation
  │ floc formation, streaming current
  ▼
Clarification (sedimentation)
  │ settled_turbidity = raw_turbidity × ~0.18 (82% reduction)
  ▼
Filtration (multimedia/sand filters)
  │ filtered_turbidity 0.1-0.5 NTU (95-98% reduction from raw)
  ▼
Disinfection (chlorine contact)
  │ free_chlorine 0.5-1.0 mg/L, CT value, ORP
  ▼
Clear Water Tank
  │ quality_index, level monitoring
  ▼
High Service Pumping
  │ HSP discharge pressure, motor power, outlet manifold
  ▼
Outlet Handover → Distribution Network
  │ outlet_turbidity, outlet_free_chlorine, compliance_status
```

---

## 3. Five Monitoring Layers

### Layer 1: Process Monitoring
Flow rates, pressures, levels, pump running statuses through the entire treatment chain.

### Layer 2: Equipment Health Monitoring
Motor currents, winding temperatures, vibrations, runtime hours, transformer temperature/load.

### Layer 3: Water Quality Monitoring Chain
Turbidity, pH, conductivity, ammonia, COD, TOC, algae, free/total chlorine, ORP, CT value — tracked at every treatment stage:
- Raw water → Settled water → Filtered water → Disinfected water → Clear water → Outlet

### Layer 4: Energy & Chemical Consumption
- `specific_energy_consumption` (kWh/m³)
- `energy_cost_per_m3` (VND/m³)
- `coagulant_dose_rate` + `coagulant_specific_consumption`
- `chlorine_dose_rate` + `chlorine_specific_consumption`
- `chemical_cost_per_m3` (VND/m³)

### Layer 5: Quality Traceability & Cost KPI
- `outlet_quality_risk_score` — composite risk index
- `raw_water_impact_score` — how much raw quality affects outlet
- `chemical_dosing_abnormality_score`
- `energy_abnormality_score`
- `probable_root_cause_code` — 0-6 code
- `cost_per_m3` — total production cost per m³

---

## 4. Asset Hierarchy

### 4.1 Areas (9)

| # | Area ID | Code | Description |
|---|---------|------|-------------|
| 1 | INTAKE-AREA | INTAKE | Raw water intake structure, screens, pumps, quality station |
| 2 | CHEMICAL-DOSING-AREA | CHEM | Coagulant, pH correction, chlorine dosing skids |
| 3 | CLARIFICATION-AREA | CLAR | Flash mixer, flocculator, clarifier, sludge pump |
| 4 | FILTRATION-AREA | FILTER | Filters 101/102, backwash pump, filter quality station |
| 5 | DISINFECTION-CLEARWATER-AREA | CLEARWATER | Contact tank, clear water tank, transfer pump |
| 6 | DISTRIBUTION-AREA | DIST | HSP station, outlet manifold, outlet quality |
| 7 | ELECTRICAL-UTILITY-AREA | ELEC | Transformer, MCC, energy monitoring |
| 8 | QUALITY-LAB-AREA | QUALITY | Lab sampling, traceability engine |
| 9 | PLANT-KPI-AREA | KPI | Plant-level KPIs |

### 4.2 Asset Tree (47 assets)

```
WTP-DEMO-01
├── INTAKE-AREA
│   ├── INTAKE-STRUCTURE-101 (vessel)
│   │   ├── SCREEN-101 (filter)
│   │   └── RAW-WATER-QUALITY-STATION-101 (sensor_array)
│   └── RAW-WATER-PUMP-STATION-101 (pump)
│       ├── RWP-101 (pump)
│       │   └── RWP-101-MOTOR (motor)
│       ├── RWP-102 (pump)
│       │   └── RWP-102-MOTOR (motor)
│       └── RAW-WATER-MANIFOLD-101 (pipeline)
│
├── CHEMICAL-DOSING-AREA
│   ├── COAGULANT-DOSING-SKID-101 (pump)
│   │   ├── COAG-TANK-101 (tank)
│   │   ├── COAG-PUMP-101 (pump)
│   │   └── COAGULATION-CONTROL-STATION-101 (sensor_array)
│   ├── PH-CORRECTION-SKID-101 (pump)
│   │   └── PH-PUMP-101 (pump)
│   ├── CHLORINE-DOSING-SKID-101 (pump)
│   │   ├── CHLORINE-TANK-101 (tank)
│   │   └── CHLORINE-PUMP-101 (pump)
│   └── CHEMICAL-CONSUMPTION-STATION-101 (sensor_array)
│
├── CLARIFICATION-AREA
│   ├── FLASH-MIXER-101 (reactor)
│   ├── FLOCCULATOR-101 (reactor)
│   └── CLARIFIER-101 (vessel)
│       ├── CLARIFIER-SCRAPER-101 (gearbox)
│       ├── SLUDGE-PUMP-101 (pump)
│       └── CLARIFIER-QUALITY-STATION-101 (sensor_array)
│
├── FILTRATION-AREA
│   ├── FILTER-101 (filter)
│   ├── FILTER-102 (filter)
│   ├── BACKWASH-PUMP-101 (pump)
│   └── FILTER-QUALITY-STATION-101 (sensor_array)
│
├── DISINFECTION-CLEARWATER-AREA
│   ├── CONTACT-TANK-101 (tank)
│   │   └── DISINFECTION-QUALITY-STATION-101 (sensor_array)
│   └── CLEAR-WATER-TANK-101 (tank)
│       ├── CLEAR-WATER-QUALITY-STATION-101 (sensor_array)
│       └── TRANSFER-PUMP-101 (pump)
│
├── DISTRIBUTION-AREA
│   └── HIGH-SERVICE-PUMP-STATION-101 (pump)
│       ├── HSP-101 (pump)
│       │   └── HSP-101-MOTOR (motor)
│       ├── HSP-102 (pump)
│       │   └── HSP-102-MOTOR (motor)
│       └── OUTLET-MANIFOLD-101 (pipeline)
│           └── TRANSFER-OUTLET-QUALITY-STATION-101 (sensor_array)
│
├── ELECTRICAL-UTILITY-AREA
│   ├── TRANSFORMER-101 (transformer)
│   └── MCC-101 (motor_control_center)
│       └── ENERGY-MONITORING-STATION-101 (sensor_array)
│
├── QUALITY-LAB-AREA
│   ├── LAB-SAMPLING-STATION-101 (analyzer)
│   └── QUALITY-TRACEABILITY-ENGINE-101 (analyzer)
│
└── PLANT-KPI-AREA
    └── PLANT-KPI-101 (analyzer)
```

---

## 5. Signal Summary

### 5.1 By Category

| Category | Count | Examples |
|----------|-------|----------|
| Process (flow, pressure, level, status) | 28 | flow_rate, discharge_pressure, tank_level, running_status |
| Equipment Health | 8 | motor_current, power, vibration_de, winding_temp, runtime_hours |
| Water Quality | 27 | turbidity, pH, conductivity, ammonia, COD, TOC, algae, free/total chlorine, ORP, CT |
| Energy Monitoring | 5 | total_active_power, total_energy_today, specific_energy_consumption, energy_cost_per_m3, peak_demand |
| Chemical Consumption | 6 | coagulant_dose_rate, coagulant_specific_consumption, chlorine_dose_rate, chlorine_specific_consumption, chemical_cost_per_m3, dosing_efficiency_index |
| Traceability | 7 | outlet_quality_risk_score, raw_water_impact_score, chemical_dosing_abnormality_score, energy_abnormality_score, probable_root_cause_code, ecoli_detected, total_coliform_detected |
| Plant KPIs | 5 | water_production_today, treatment_yield, outlet_quality_index, compliance_rate_today, cost_per_m3 |
| Derived/Calculated | 11 | quality indices, compliance status, CT value, efficiency indices, algae_index, floc_size_index, clarifier_efficiency_index, filter_run_quality_index, particle_count_proxy, clear_water_quality_index |
| **TOTAL** | **~97** | |

### 5.2 Water Quality Chain (key trend bundle)

```
RAW-WATER-QUALITY-STATION-101.raw_turbidity
    ↓
CLARIFIER-QUALITY-STATION-101.settled_turbidity
    ↓
FILTER-QUALITY-STATION-101.filtered_turbidity
    ↓
TRANSFER-OUTLET-QUALITY-STATION-101.outlet_turbidity
```

This 4-signal chain is the primary demo visualization target.

### 5.3 Quality Traceability Signals

```
QUALITY-TRACEABILITY-ENGINE-101.outlet_quality_risk_score  → overall risk
QUALITY-TRACEABILITY-ENGINE-101.raw_water_impact_score     → raw water contribution
QUALITY-TRACEABILITY-ENGINE-101.chemical_dosing_abnormality_score
QUALITY-TRACEABILITY-ENGINE-101.energy_abnormality_score
QUALITY-TRACEABILITY-ENGINE-101.probable_root_cause_code   → 0=normal, 1-6=fault
```

---

## 6. Abnormal Scenarios (8)

| # | Scenario ID | Description | Key Impact |
|---|------------|-------------|------------|
| 1 | normal_operation | Stable production, compliant quality | Baseline |
| 2 | raw_water_contamination | Raw turbidity/COD/ammonia spike | Quality chain degrades, risk score rises |
| 3 | algae_bloom | Algae/TOC increase | Chlorine demand rises, residual drops |
| 4 | filter_breakthrough | Filter quality deteriorates | Outlet turbidity risk, compliance at risk |
| 5 | chlorine_underdosing | Chlorine dose drops | Free chlorine drops, compliance fails |
| 6 | chemical_overdosing | Excess chemical dosing | Outlet quality OK but cost per m³ high |
| 7 | filter_clogging_energy_impact | Filter DP rises | Pumping energy up, quality risk grows |
| 8 | hsp_trip | HSP-101 trips | Outlet pressure drops, HSP-102 compensates partially |

---

## 7. Dashboard / View Design

### 7.1 Plant Overview
- Production today (m³)
- Outlet quality index
- Cost per m³
- Active alarm count
- Mini trend: outlet turbidity (last 1h)

### 7.2 Water Quality Chain
- **Main trend bundle**: raw_turbidity → settled_turbidity → filtered_turbidity → outlet_turbidity
- pH chain: raw_pH → settled_pH → filtered_pH → outlet_pH
- Chlorine chain: free_chlorine → total_chlorine → outlet_free_chlorine
- Outlet compliance status indicator

### 7.3 Energy & Chemical Cost
- specific_energy_consumption trend
- energy_cost_per_m3 trend
- chemical_cost_per_m3 trend
- cost_per_m3 (stacked: energy + chemical)

### 7.4 Quality Traceability
- outlet_quality_risk_score gauge
- Four contributing scores (stacked bar)
- probable_root_cause_code indicator
- E. coli / coliform status

### 7.5 Equipment Health
- Pump motor currents (RWP-101, RWP-102, HSP-101, HSP-102)
- Filter DP (FILTER-101, FILTER-102)
- Transformer temperature & load

### 7.6 GIS Site Layout
- 9 area polygons on a simplified site map
- Asset markers with status colors
- Click → navigate to asset detail

---

## 8. PlantOS Import Path

```
Task 8A-02: Contract File
  → examples/contracts/wtp-demo-01.contract.yaml (validated against JSON Schema)

Task 8A-03: Validate & Preview
  → POST /api/v1/contracts/validate  → 0 errors, warnings documented
  → POST /api/v1/contracts/preview   → all "create", 0 conflicts

Task 8A-04: Apply
  → POST /api/v1/contracts/apply     → 1 plant + 9 areas + 47 assets + 97 signals
  → GET  /api/v1/assets?plant_id=WTP-DEMO-01  → verify hierarchy
  → GET  /api/v1/signals?plant_id=WTP-DEMO-01 → verify 97 signals
```

---

## 9. Virtual Factory Simulation Path

```
[Separate track — Virtual Factory project]

Task VF-8A-05: WTP Simulator
  → Read wtp-demo-01.contract.yaml
  → Build simulator with 6 pattern types
  → Implement dependent signal engine
  → 8 scenarios with hot-switch API
  → HTTP ingest → PlantOS /api/v1/measurements/ingest
```

Prompt đã tạo: `docs/prompts/phase8a-vf-wtp-simulator-pm-prompt.md`

---

## 10. UNS Path Convention

```
Template: {namespace_root}/{plant_id}/{area_id}/{asset_id}/{signal_name}

Example:
  avenue/wtp-demo-01/intake-area/raw-water-quality-station-101/raw_turbidity
  avenue/wtp-demo-01/filtration-area/filter-101/filter_dp
  avenue/wtp-demo-01/plant-kpi-area/plant-kpi-101/cost_per_m3
```

---

## 11. Alarm Recommendations (7 rules)

| Rule ID | Signal | Condition | Threshold | Severity |
|---------|--------|-----------|-----------|----------|
| WTP_FILTER_101_HIGH_DP | FILTER-101.filter_dp | > | 80 kPa | high |
| WTP_FILTERED_TURBIDITY_HIGH | FILTER-QUALITY-STATION-101.filtered_turbidity | > | 1.0 NTU | high |
| WTP_OUTLET_TURBIDITY_HIGH | TRANSFER-OUTLET-QUALITY-STATION-101.outlet_turbidity | > | 1.0 NTU | critical |
| WTP_OUTLET_CHLORINE_LOW | TRANSFER-OUTLET-QUALITY-STATION-101.outlet_free_chlorine | < | 0.2 mg/L | critical |
| WTP_SPECIFIC_ENERGY_HIGH | ENERGY-MONITORING-STATION-101.specific_energy_consumption | > | 0.5 kWh/m³ | medium |
| WTP_CHEMICAL_COST_HIGH | CHEMICAL-CONSUMPTION-STATION-101.chemical_cost_per_m3 | > | 150 VND/m³ | medium |
| WTP_OUTLET_COMPLIANCE_FAIL | TRANSFER-OUTLET-QUALITY-STATION-101.outlet_compliance_status | == | false | critical |

> **Note:** These are demo recommendations marked as configurable. They are NOT official regulatory compliance thresholds.

---

## 12. Assumptions & Out-of-Scope

### Assumptions
- WTP capacity: ~800-1000 m³/h (~20,000 m³/day)
- Surface water source (river/reservoir) with variable quality
- Conventional treatment: coagulation → flocculation → clarification → filtration → chlorination
- All quality limits are **demo thresholds** — not regulatory
- Cost calculations use demo unit prices: energy ~2,000 VND/kWh, coagulant ~15,000 VND/kg, chlorine ~25,000 VND/kg

### Out-of-Scope
- Sludge treatment and disposal
- Backwash water recovery
- Chemical storage and handling details
- SCADA/HMI screens
- Regulatory compliance reporting
- MES/work-order integration
- Advanced process control (PID loops)
- Membrane filtration / advanced oxidation
- Fluoridation
- Corrosion control

---

## 13. Risk Assessment

| Risk | Mitigation |
|------|------------|
| 97 signals overwhelm simulator at 1s interval | Start at 10s, tune down |
| `signal_type: calculated` rejected by validator | Use `signal_type: measurement` for all |
| Simulation format mismatch with Pydantic model | Use `extensions.vf_simulation` for VF-specific fields |
| Contract too large → API timeout | Test progressively, batch ingest |
| Preview shows conflicts from prior runs | Use fresh DB or on_conflict=skip |

---

## 14. Task Breakdown (Adjusted)

```
PlantOS Track:
  Task 8A-01 ✅ Design Document (this file)
  Task 8A-02    Contract File — Coder PlantOS
  Task 8A-03    Validate & Preview — Coder PlantOS
  Task 8A-04    Apply — Coder PlantOS
  Task 8A-06    Monitoring Artifacts — Coder PlantOS
  Task 8A-07    E2E Demo Test — Coder PlantOS
  Task 8A-08    Review & Acceptance — Reviewer (this session)

Virtual Factory Track (song song):
  Task VF-8A-05 WTP Simulator — PM + Coder VF
                 Prompt: docs/prompts/phase8a-vf-wtp-simulator-pm-prompt.md
```

---

## 15. Acceptance Criteria (Phase 8A)

1. ✅ WTP contract validates successfully
2. ✅ Preview is clean and understandable
3. ✅ Apply creates PlantOS registry without breaking VF-DEMO
4. ✅ PlantOS shows correct areas/assets/signals
5. ✅ Simulator generates telemetry for ≥60 signals
6. ✅ Measurement ingestion works
7. ✅ Current/history query works
8. ✅ Trend bundle: raw → settled → filtered → outlet turbidity
9. ✅ Outlet quality and compliance signals visible
10. ✅ Energy and chemical cost KPIs visible
11. ✅ ≥5 abnormal scenarios demonstrable
12. ✅ ≥5 alarm recommendations documented
13. ✅ No VF-specific fields in PlantOS core signal model
14. ✅ No new importer UI created
15. ✅ No automatic manifest generation implemented
