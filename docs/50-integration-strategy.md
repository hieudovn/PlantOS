# PlantOS Integration Strategy

## 1. Integration objective

PlantOS should become the operational data foundation for other industrial applications.

It must integrate with existing systems without forcing customers to replace their current architecture.

Key integration targets:

- MES,
- Virtual Factory,
- SCADA/DCS,
- PLC/RTU/gateway,
- Historian,
- CMMS/EAM,
- ERP,
- AI assistants,
- BI/analytics tools,
- GIS systems,
- external APIs.

## 2. Integration principle

PlantOS must avoid point-to-point chaos.

Integration should follow this flow:

```text
External System / Edge Source
        ↓
Adapter / Connector
        ↓
Normalization
        ↓
Asset + Signal + Event Context
        ↓
UNS / CDM
        ↓
Application API / Event Contract
```

## 3. MES integration

MES should not read raw PLC tags directly from PlantOS storage.

MES should consume PlantOS through CDM-aligned APIs and events.

### PlantOS provides to MES

- equipment status,
- signal values,
- machine state,
- downtime events,
- alarm events,
- quality measurements,
- energy data,
- workstation/device context,
- historical trend data,
- production-relevant equipment events.

### MES provides to PlantOS

- production order,
- manufacturing order,
- operation,
- material context,
- batch/lot context,
- operator/checklist events,
- quality inspection events,
- production schedule context.

### Shared contract

```text
Asset + Signal + Event + Production Context
```

PlantOS owns equipment and operational data context.

MES owns production execution context.

The integration boundary should be explicitly documented and versioned.

## 4. Virtual Factory integration

Virtual Factory should use the same PlantOS data contracts as real equipment.

Simulation should publish:

- asset states,
- signal values,
- alarms,
- events,
- quality measurements,
- production events,
- energy consumption.

PlantOS should not care whether data is real or simulated except through quality/source metadata.

Recommended quality flag:

```text
SIMULATED
```

This enables the same dashboard, dynamic diagram, GIS, historian, rule engine and MES integration to work with both real and simulated plants.

## 5. Historian integration

PlantOS can work in three modes:

### Mode 1: Built-in historian

For plants without existing historian.

PlantOS stores operational time-series data using TDengine, VictoriaMetrics or another selected TSDB.

### Mode 2: Historian integration

For plants already using PI, Canary, IP.21 or another historian.

PlantOS connects to the existing historian, maps tags to assets/signals, and builds UNS/CDM context above it.

### Mode 3: Hybrid historian

PlantOS stores selected derived/contextualized data while enterprise historian remains the system of record for raw plant time-series.

## 6. SCADA/DCS/PLC integration

PlantOS must not replace control systems.

PlantOS consumes data from control and automation systems through:

- OPC UA,
- Modbus TCP,
- MQTT,
- REST API,
- file import,
- historian connector,
- vendor-specific connector where needed.

Write-back/control commands must be treated as high-risk and require strict authorization, audit and safety review.

## 7. CMMS/EAM integration

PlantOS can provide asset health, alarms and operational events to CMMS/EAM systems.

Potential integrations:

- IBM Maximo / MAS,
- Odoo Maintenance,
- SAP PM,
- other EAM/CMMS systems.

Use cases:

- create work request from alarm,
- enrich asset context,
- display maintenance status in PlantOS,
- correlate operational events with maintenance history,
- support AHM/APM workflows.

## 8. ERP integration

ERP integration should be indirect and governed.

ERP may provide:

- production plan,
- material master,
- BOM,
- cost center,
- inventory context,
- purchase/order context.

PlantOS should not become ERP.

## 9. AI integration

AI must consume contextualized APIs, not raw time-series tables.

Recommended AI access pattern:

```text
AI Assistant → PlantOS API / Semantic Query → CDM + Context + Historian Query
```

AI should be able to answer:

- what asset is abnormal,
- which signal changed,
- what alarm occurred,
- what related events happened,
- what production or maintenance context is relevant,
- what trend supports the conclusion.

AI must not directly modify rules, configuration or operational workflows without approval.

## 10. Integration governance

Every integration must define:

- source system,
- target system,
- data owner,
- data contract,
- schema version,
- security model,
- frequency/latency,
- failure handling,
- retry behavior,
- audit requirements.

Ad-hoc integration scripts are allowed only for experiments and must be replaced by governed connectors before production use.
