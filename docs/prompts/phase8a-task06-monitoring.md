# Task 8A-06 — WTP Monitoring Demo Artifacts

## Context

You are the Coder-Executioner for PlantOS Phase 8A.

The WTP-DEMO-01 plant is fully applied (149 entities). The VF simulator is generating live data via HTTP ingestion. All 92 signals have current and historical data available.

Your job: Create the monitoring demo artifacts — process diagram, GIS layout, and trend configurations — that demonstrate PlantOS visualization capabilities for the WTP reference model.

## Required Reading

```text
docs/reference-models/wtp-demo-01-design.md           ← Areas, assets, process flow
docs/17-visualization-binding-spec.md                  ← Binding format
examples/contracts/wtp-demo-01.contract.yaml           ← Signal list, dashboards in extensions
```

## Deliverables

### 1. Process Flow Diagram

```
examples/diagrams/wtp-demo-01-process.svg
```

A simplified SVG process flow diagram showing the WTP treatment chain. Requirements:

- **Format**: SVG, viewBox ~ 1200x800
- **Style**: Clean industrial schematic, not photorealistic
- **Color scheme**: Blue water lines, gray equipment, green/red status indicators
- **Must show these 8 process stages** (left to right):

```
[Intake] → [Chemical Dosing] → [Flash Mix/Floc] → [Clarifier] → [Filters] → [Contact Tank] → [Clear Water] → [HSP → Outlet]
```

- **Each stage** should show:
  - Area name label
  - 1-2 key equipment icons (pump, tank, filter, etc.)
  - 1-2 key signal value placeholders (will bind to live data)

- **Key signal placeholders** (use `data-binding` attribute for later linking):
  - `raw_turbidity` at Intake
  - `settled_turbidity` at Clarifier
  - `filtered_turbidity` at Filters
  - `outlet_turbidity` at Outlet
  - `free_chlorine` at Contact Tank
  - `filter_dp` at Filters
  - `cost_per_m3` at Outlet/KPI area

### 2. Diagram Binding YAML

```
examples/diagrams/wtp-demo-01-process.binding.yaml
```

Maps SVG elements to PlantOS signals for live data display.

Format (from `docs/17-visualization-binding-spec.md`):

```yaml
bindings:
  - binding_id: wtp-raw-turbidity
    binding_type: asset_signal
    selector: "#raw-turbidity-value"
    asset_id: RAW-WATER-QUALITY-STATION-101
    signal_name: raw_turbidity
    mode: realtime
    display:
      format: "0.0"
      unit: NTU

  - binding_id: wtp-settled-turbidity
    binding_type: asset_signal
    selector: "#settled-turbidity-value"
    asset_id: CLARIFIER-101
    signal_name: settled_turbidity
    mode: realtime
    display:
      format: "0.0"
      unit: NTU

  # ... Continue for ALL placeholder signals in the SVG
```

Include bindings for at least 12 signals covering all 8 stages.

### 3. GIS Site Layout

```
examples/gis/wtp-demo-01-site-layout.json
```

A GeoJSON-like site layout with area polygons and asset markers.

Format:

```json
{
  "site": {
    "name": "WTP-DEMO-01",
    "center": { "lat": 10.762622, "lng": 106.660172 },
    "zoom": 16
  },
  "areas": [
    {
      "area_id": "INTAKE-AREA",
      "name": "Raw Water Intake",
      "polygon": [
        { "lat": 10.7630, "lng": 106.6590 },
        { "lat": 10.7633, "lng": 106.6598 },
        { "lat": 10.7628, "lng": 106.6602 },
        { "lat": 10.7625, "lng": 106.6594 }
      ],
      "color": "#3b82f6"
    },
    ... 8 more areas
  ],
  "assets": [
    {
      "asset_id": "INTAKE-STRUCTURE-101",
      "name": "Intake Structure",
      "position": { "lat": 10.7631, "lng": 106.6594 },
      "icon": "vessel",
      "area_id": "INTAKE-AREA"
    },
    ... key assets
  ]
}
```

Requirements:
- 9 area polygons arranged logically (intake at river side → treatment chain → outlet)
- At least 15 asset markers covering all areas
- Realistic coordinates (use Ho Chi Minh City area as reference)
- Each area has a distinct color

### 4. Trend Bundle Configurations

Document the trend bundles defined in the contract's `extensions.monitoring.dashboards` section. Create a quick-reference config file:

```
examples/diagrams/wtp-demo-01-trends.yaml
```

```yaml
# WTP-DEMO-01 Trend Bundle Quick Reference
# Generated from extensions.monitoring.dashboards in wtp-demo-01.contract.yaml

bundles:
  turbidity_chain:
    name: Treatment Effectiveness
    signals:
      - RAW-WATER-QUALITY-STATION-101.raw_turbidity
      - CLARIFIER-101.settled_turbidity
      - FILTER-QUALITY-STATION-101.filtered_turbidity
      - TRANSFER-OUTLET-QUALITY-STATION-101.outlet_turbidity

  chlorine_chain:
    name: Chlorine Disinfection
    signals:
      - DISINFECTION-QUALITY-STATION-101.free_chlorine
      - DISINFECTION-QUALITY-STATION-101.total_chlorine
      - TRANSFER-OUTLET-QUALITY-STATION-101.outlet_free_chlorine

  energy_cost:
    name: Energy & Cost
    signals:
      - ENERGY-MONITORING-STATION-101.specific_energy_consumption
      - ENERGY-MONITORING-STATION-101.energy_cost_per_m3
      - CHEMICAL-CONSUMPTION-STATION-101.chemical_cost_per_m3
      - PLANT-KPI-101.cost_per_m3

  traceability:
    name: Quality Traceability
    signals:
      - QUALITY-TRACEABILITY-ENGINE-101.outlet_quality_risk_score
      - QUALITY-TRACEABILITY-ENGINE-101.raw_water_impact_score
      - QUALITY-TRACEABILITY-ENGINE-101.chemical_dosing_abnormality_score
      - QUALITY-TRACEABILITY-ENGINE-101.energy_abnormality_score
      - QUALITY-TRACEABILITY-ENGINE-101.probable_root_cause_code

  equipment_health:
    name: Equipment Health
    signals:
      - RWP-101-MOTOR.motor_current
      - HSP-101-MOTOR.motor_current
      - FILTER-101.filter_dp
      - FILTER-102.filter_dp
      - TRANSFORMER-101.winding_temp
```

## Implementation Notes

### SVG Diagram Tips

- Keep it simple — a schematic, not a CAD drawing
- Use `<rect>`, `<circle>`, `<line>`, `<text>` elements
- Add `id` attributes on elements that need live data binding
- Use CSS classes for status colors (`.status-normal`, `.status-warning`, `.status-alarm`)
- Include a legend
- Total SVG should be under 500 lines

### GIS Layout Tips

- Arrange areas along a logical flow path
- Place intake near "water" (south/west edge)
- Place outlet at opposite end (north/east edge)
- Keep polygons simple (4-6 vertices each)
- Add a `"description"` field for each area

### Gap Documentation

If the current PlantOS visualization runtime cannot fully support a feature, document the limitation in a comment rather than forcing an unsupported approach:

```yaml
# NOTE: This binding uses format "0.0" which requires visualization-sdk v0.3+
# Current version may fall back to default formatting.
```

## Deliverables Summary

| File | Description |
|------|-------------|
| `examples/diagrams/wtp-demo-01-process.svg` | Process flow diagram with signal placeholders |
| `examples/diagrams/wtp-demo-01-process.binding.yaml` | SVG-to-signal binding map |
| `examples/gis/wtp-demo-01-site-layout.json` | Area polygons + asset markers |
| `examples/diagrams/wtp-demo-01-trends.yaml` | Trend bundle quick reference |

## Acceptance Criteria

- [ ] SVG diagram shows all 8 treatment stages
- [ ] Binding YAML covers at least 12 signals
- [ ] GIS layout has 9 areas + 15+ asset markers
- [ ] Trend config matches contract's monitoring dashboards
- [ ] All files are valid YAML/JSON/SVG
- [ ] No hardcoded raw tag names (use asset_id + signal_name)
