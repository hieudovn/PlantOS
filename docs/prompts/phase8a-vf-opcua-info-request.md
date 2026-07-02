# Info Request — VF WTP Simulator: OPC UA NodeId Mapping & Ingestion Setup

## Context

You are the AI Coding Assistant for the **Virtual Factory** project.

The WTP-DEMO-01 simulator is running and exposing data via OPC UA (port 4841, namespace WTP-Simulator). PlantOS needs to configure data ingestion from this simulator.

Please answer the following questions to help the PlantOS team complete the integration.

## Questions

### Q1: OPC UA NodeId Convention

What is the NodeId naming convention used for WTP signals?

Example from the contract's existing bindings:
```
signal_id: RWP-101.flow_rate  →  node_id: ns=2;s=RWP101_FLOW_RATE
```

Does this convention apply to ALL 92 signals? If so, provide the transformation rule (e.g., `{asset_id}_{signal_name}` with hyphens removed, uppercase).

### Q2: Full NodeId Mapping

For these 10 key signals, provide the exact OPC UA NodeId:

| # | Signal ID | OPC UA NodeId |
|---|-----------|---------------|
| 1 | INTAKE-STRUCTURE-101.raw_water_level | ? |
| 2 | RAW-WATER-QUALITY-STATION-101.raw_turbidity | ? |
| 3 | RAW-WATER-QUALITY-STATION-101.raw_ph | ? |
| 4 | RWP-101.flow_rate | ? |
| 5 | CLARIFIER-101.settled_turbidity | ? |
| 6 | FILTER-QUALITY-STATION-101.filtered_turbidity | ? |
| 7 | DISINFECTION-QUALITY-STATION-101.free_chlorine | ? |
| 8 | TRANSFER-OUTLET-QUALITY-STATION-101.outlet_turbidity | ? |
| 9 | ENERGY-MONITORING-STATION-101.specific_energy_consumption | ? |
| 10 | PLANT-KPI-101.cost_per_m3 | ? |

### Q3: OPC UA Server Details

- Endpoint URL: `opc.tcp://<HOST>:4840` or `opc.tcp://<HOST>:4841`?
- Authentication: Anonymous / Username+Password / Certificate?
- Are all 92 signals browseable under the WTP-Simulator namespace?

### Q4: HTTP Ingestion Support

Does the VF WTP simulator support direct HTTP ingestion to PlantOS?

```
POST http://<plantos-host>:8000/api/v1/measurements/ingest
```

If yes, is it already configured? If not, is it planned?

### Q5: Signal List Alignment

Are the 92 signals in `wtp-demo-01.contract.yaml` exactly matching what the simulator generates? Any signals added, removed, or renamed?

### Q6: Scenario Control

How does PlantOS switch scenarios on the running simulator?

- HTTP endpoint? (e.g., `POST http://<vf-host>:5000/scenario/{id}`)
- OPC UA method call?
- Manual restart?

Please list the exact API call to switch to each of the 8 scenarios.

## Expected Response Format

Please answer each question concisely. For Q2, provide a table or code block with the complete mapping. For Q6, provide curl examples.

## Urgency

Medium — PlantOS Apply (Task 8A-04) can proceed in parallel, but ingestion setup needs this info.
