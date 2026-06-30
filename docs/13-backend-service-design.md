# PlantOS Backend Service Design

## 1. Objective

The backend is the governed API and service layer of PlantOS Center.

It owns metadata, ingestion, query, registry, UNS, historian abstraction, alarm/rule placeholder and integration contracts.

## 2. Recommended MVP backend stack

Initial recommendation:

```text
Python FastAPI
SQLAlchemy / SQLModel
Alembic migrations
PostgreSQL
TDengine client abstraction
Pydantic schemas
pytest
Docker
```

Alternative stack can be NestJS if the frontend/backend team strongly prefers TypeScript. This requires an ADR before implementation.

## 3. Service modules

```text
backend/app/modules
├── assets
├── signals
├── measurements
├── historian
├── uns
├── alarms
├── edge_nodes
└── health
```

## 4. Module responsibilities

### Assets module

Responsibilities:

- create/list/update assets,
- manage asset hierarchy,
- assign area/plant context,
- expose asset detail API.

Non-responsibilities:

- storing time-series values,
- rendering diagrams,
- managing MES production orders.

### Signals module

Responsibilities:

- create/list/update signals,
- map signal to asset/device/source tag,
- define engineering unit, data type and quality policy,
- generate or validate UNS path.

### Measurements module

Responsibilities:

- accept measurement ingestion,
- validate signal identity,
- normalize quality and timestamp,
- write to historian abstraction,
- expose current and historical query APIs.

### Historian module

Responsibilities:

- abstract TSDB backend,
- write measurements,
- query current value,
- query historical range,
- hide TDengine/VictoriaMetrics physical model from application modules.

### UNS module

Responsibilities:

- generate UNS paths,
- validate namespace policy,
- expose UNS lookup for assets/signals,
- prevent unmanaged topic naming.

### Alarms module

MVP responsibilities:

- define alarm model placeholder,
- evaluate simple threshold rule if included,
- expose alarm/event list placeholder.

Full rule engine is not MVP Phase 1.

### Edge Nodes module

MVP responsibilities:

- register edge/simulator node,
- record heartbeat,
- show status,
- support future edge management.

## 5. Backend architecture rules

- API routes must call service layer, not database directly.
- Service layer must use repository/data access layer.
- Measurement APIs must write through historian abstraction.
- UI-specific formatting should not be done in backend except API response schemas.
- No module should create raw tag dependencies outside the signal registry.
- All externally visible APIs must use stable schemas.

## 6. Suggested folder pattern per module

```text
modules/assets/
├── router.py
├── schemas.py
├── service.py
├── repository.py
└── models.py
```

## 7. Initial backend endpoints

```text
GET    /health

GET    /api/v1/assets
POST   /api/v1/assets
GET    /api/v1/assets/{asset_id}
PATCH  /api/v1/assets/{asset_id}

GET    /api/v1/signals
POST   /api/v1/signals
GET    /api/v1/signals/{signal_id}
PATCH  /api/v1/signals/{signal_id}

POST   /api/v1/measurements/ingest
GET    /api/v1/measurements/current
GET    /api/v1/measurements/history

GET    /api/v1/uns/paths
GET    /api/v1/alarms
GET    /api/v1/edge-nodes
POST   /api/v1/edge-nodes/heartbeat
```

## 8. Current value strategy

MVP can use one of two approaches:

### Option A: Query latest from TSDB

Simple but may be slower.

### Option B: Write-through current value cache

Measurement ingestion writes to TSDB and updates Redis/PostgreSQL current value table.

Recommended MVP: start with Option A unless performance is poor, but keep API contract independent.

## 9. Error handling

APIs should return structured errors:

```json
{
  "error_code": "SIGNAL_NOT_FOUND",
  "message": "Signal does not exist",
  "details": {}
}
```

## 10. Validation requirements

- asset_id must be unique,
- signal_id must be unique,
- signal must reference valid asset,
- measurement must reference valid signal,
- quality must be normalized,
- timestamp must be parseable and timezone-aware,
- UNS path must follow policy.

## 11. Testing requirements

Minimum tests:

- create asset,
- create signal linked to asset,
- reject signal with invalid asset,
- ingest measurement for valid signal,
- reject measurement for unknown signal,
- query current value,
- query historical values,
- validate UNS path generation.

## 12. Future modules

Later backend modules:

- rule engine,
- notification,
- user/tenant/security,
- visualization definitions,
- diagram storage,
- GIS layer management,
- integration connectors,
- MES event contract,
- AI semantic query API.
