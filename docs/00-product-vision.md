# PlantOS Product Vision

## 1. Vision statement

PlantOS is an industrial operational platform that turns raw plant data into governed, contextualized, application-ready operational intelligence.

It is designed to become the common foundation for IIoT, Manufacturing Data Platform, MES integration, Virtual Factory, Asset Health Monitoring, analytics, AI assistants, and future digital twin applications.

## 2. Why PlantOS exists

Many industrial systems are built around isolated components:

- PLC / SCADA collect and control process signals.
- Historians store time-series tags.
- Dashboards visualize values.
- MES handles production workflows.
- CMMS/EAM manages maintenance.
- Analytics tools work on exported data.

This creates fragmentation:

- tag-centric data without business context,
- duplicated asset models,
- inconsistent naming,
- hard-coded dashboards,
- isolated edge systems,
- weak governance of rules, flows and data definitions,
- difficult integration with MES, AI and digital twin applications.

PlantOS exists to provide a common operational layer above raw automation systems and below business applications.

## 3. Product definition

```text
PlantOS = Industrial Operational Data Platform + Edge Runtime + Visualization Runtime + Governance Layer
```

PlantOS is not a single-purpose product. It is a plant-level runtime foundation.

## 4. What PlantOS is

PlantOS is:

- an edge-center industrial data platform,
- an operational time-series and historian-capable service,
- a Unified Namespace platform,
- a Canonical Data Model platform,
- an asset and signal context engine,
- a visualization runtime for P&ID, one-line diagrams, GIS, trend, alarm and table views,
- a governed low-code rule and flow platform,
- an integration layer for MES, Virtual Factory, AHM/APM, AI and analytics.

## 5. What PlantOS is not

PlantOS is not:

- a SCADA replacement,
- a PLC control system,
- only a Historian,
- only an IoT dashboard,
- a MES,
- an ERP,
- a free-form no-code platform,
- a clone of ThingsBoard, Node-RED, Grafana, Ignition or EdgeX.

PlantOS may integrate with or reuse ideas from these platforms, but its product logic must remain asset-centric, UNS-native, CDM-native and governed.

## 6. Target users

Primary user groups:

- Plant operators: monitor status, alarms, trends and diagrams.
- Maintenance engineers: inspect asset health, events and abnormal conditions.
- Process/electrical engineers: configure signals, diagrams, thresholds and logic.
- Data engineers: manage UNS, schema, CDM, historian and pipelines.
- System integrators: deploy edge nodes, connect protocols and build integrations.
- Administrators: manage users, tenants, licenses, security and edge fleet.
- Solution architects: design reusable templates for industries and customers.

## 7. Target use cases

Initial use cases:

- IIoT monitoring platform,
- plant operational historian for sites without existing historian,
- contextualized data foundation for MES,
- dynamic P&ID / one-line diagram monitoring,
- GIS-based asset and alarm monitoring,
- energy monitoring,
- asset health monitoring,
- virtual factory simulation integration,
- AI-ready operational data layer.

## 8. Product principles

PlantOS must be:

1. Open-source based where possible.
2. Productizable and brandable.
3. Modular and composable.
4. Edge-center hybrid.
5. UNS-native.
6. CDM-native.
7. Asset-centric and event-centric.
8. Secure by design.
9. Governed, auditable and versioned.
10. Ready for AI, MES and digital twin applications.
