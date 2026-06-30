# PlantOS MVP Scope

## 1. MVP objective

The MVP must prove that PlantOS can act as a governed operational data foundation, not just a dashboard.

The first working product should demonstrate:

- asset and signal registry,
- measurement ingestion,
- time-series storage,
- historical query,
- current value query,
- UNS path generation,
- lightweight frontend shell,
- trend visualization,
- dynamic 2D diagram binding,
- GIS asset marker view,
- simulated plant data.

## 2. MVP non-goals

The MVP should not include:

- full MES functionality,
- full SCADA replacement,
- advanced edge management,
- full no-code builder,
- 3D digital twin,
- complex workflow engine,
- enterprise SSO,
- multi-tenant billing,
- plugin marketplace,
- advanced APM algorithms.

These can be designed later after the data foundation works.

## 3. MVP user story

As a plant engineer, I want to register demo assets and signals, ingest simulated telemetry, view current and historical values, see dynamic status on a P&ID/one-line diagram, and locate assets on a GIS map.

## 4. MVP demo scenario

Use a demo plant with:

- one site,
- two areas,
- one process line,
- one electrical subsystem,
- several assets,
- simulated measurements,
- simple alarms,
- one P&ID diagram,
- one one-line diagram,
- one GIS map.

Example assets:

```text
PUMP-101
MOTOR-101
TANK-101
VALVE-101
FEEDER-01
BREAKER-01
TRANSFORMER-01
```

Example signals:

```text
discharge_pressure
flow_rate
motor_current
running_status
tank_level
valve_position
breaker_status
voltage
power
```

## 5. MVP backend scope

Backend must provide:

- health API,
- asset registry CRUD,
- signal registry CRUD,
- measurement ingestion API,
- current value API,
- historical query API,
- simple UNS path generation,
- simple alarm evaluation placeholder,
- simulator data receiver.

## 6. MVP frontend scope

Frontend must provide:

- branded PlantOS shell,
- sidebar navigation,
- asset list,
- asset detail page,
- signal list,
- trend chart,
- alarm/event table placeholder,
- SVG diagram viewer,
- GIS map view,
- edge/simulator status placeholder.

## 7. MVP edge/simulator scope

Edge/simulator must provide:

- synthetic telemetry generation,
- MQTT or HTTP publishing,
- configurable asset/signal list,
- simulated quality status,
- simulated alarm condition,
- optional offline/backlog simulation placeholder.

## 8. MVP data storage scope

Use:

- PostgreSQL for metadata,
- TDengine or selected TSDB for measurements,
- optional Redis for current value cache,
- EMQX for MQTT ingestion path.

Direct UI-to-storage query is not allowed.

## 9. MVP acceptance criteria

The MVP is accepted when:

1. A demo plant can be loaded from sample data.
2. Assets and signals are visible in the UI.
3. Simulated measurements are ingested into the platform.
4. Current value API returns latest values by asset/signal.
5. Historical query API returns time-series data for trends.
6. Trend chart displays historical measurements.
7. Dynamic diagram changes values/status based on bindings.
8. GIS map shows asset markers and simple status.
9. All UI data comes through PlantOS APIs.
10. Documentation and run instructions are available.

## 10. Phase closure criteria before coding

Before coding starts, the following documents should exist:

- repository structure,
- MVP scope,
- backend service design,
- API contract,
- database/storage design,
- frontend UX design,
- visualization binding design,
- simulator design,
- deployment design,
- acceptance checklist.
