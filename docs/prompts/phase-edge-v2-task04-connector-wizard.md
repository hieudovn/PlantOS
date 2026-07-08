# E2V2-2: Connector Setup Wizard + Safe Apply

## Context

Edge v2 needs a wizard-driven connector setup experience. Users should configure OPC UA, Modbus TCP, and MQTT connectors without editing YAML manually. Each connector must follow a unified `BaseConnector` interface. Configuration changes must go through the safe apply flow: Draft → Validate → Test → Apply → Confirm → Rollback.

## Plan Reference

- `docs/phase-edge-v2-productization-plan.md` §7.3, §9
- `docs/01-project-constitution.md`
- `docs/60-edge-center-strategy.md`

## Constitution Checklist

- [x] Connectors use signal_id, not raw tag names for processing
- [x] All connector config goes through API (no direct YAML manipulation)
- [x] Safe apply prevents broken config from reaching runtime
- [x] Connector health visible in heartbeat (Center monitoring)
- [x] No PLC write or control commands

## Implementation Checklist

### Connector Framework

- [ ] **2.1** Define `BaseConnector` in `edge-v2/agent/connectors/base.py`:
  ```python
  @dataclass
  class RawReading:
      source_ref: str
      signal_id: str
      raw_value: float
      timestamp: datetime
      quality_hint: str | None

  @dataclass
  class ConnectorStatus:
      connector_id: str
      type: str
      status: Literal["running", "stopped", "error", "degraded"]
      connected: bool
      signal_count: int
      last_success_at: datetime | None
      last_error: str | None
      last_error_at: datetime | None

  class BaseConnector(ABC):
      connector_id: str
      connector_type: str

      @abstractmethod async def start(self) -> None: ...
      @abstractmethod async def stop(self) -> None: ...
      @abstractmethod async def restart(self) -> None: ...
      @abstractmethod async def status(self) -> ConnectorStatus: ...
      @abstractmethod async def test_connection(self) -> TestResult: ...
      @abstractmethod async def validate_config(self, config: dict) -> list[str]: ...
      @abstractmethod async def read_tags(self, tag_configs: list[TagConfig]) -> list[RawReading]: ...
  ```

- [ ] **2.2** Implement `ConnectorRegistry` in `edge-v2/agent/connectors/registry.py`:
  - Register connector classes by type string
  - Instantiate connectors from config
  - Lifecycle management (start_all, stop_all, get_status_all)
  - `CONNECTOR_REGISTRY = {"opcua": OpcUaConnector, "modbus_tcp": ModbusTcpConnector, "mqtt": MqttSubscribeConnector}`

### OPC UA Connector

- [ ] **2.3** Implement `OpcUaConnector`:
  - Refactor from `edge/agent/collectors/opcua/` into `BaseConnector` interface
  - `test_connection()` — connect, read server status, disconnect
  - `validate_config()` — check endpoint format, required tags
  - `read_tags()` — return `list[RawReading]`
  - Browse: configurable namespace filter, max depth 3, start from Objects folder
  - Reconnect with exponential backoff (1s, 2s, 4s, 8s, max 30s)

### Modbus TCP Connector

- [ ] **2.4** Implement `ModbusTcpConnector`:
  - Refactor from `edge/agent/collectors/modbus/` into `BaseConnector` interface
  - `test_connection()` — connect, read single known register, disconnect
  - `validate_config()` — check host format, register ranges
  - `read_tags()` — batch read by register type (holding/coil)
  - Float32 decode, Int16, UInt32 support
  - Scale + offset applied in connector (raw mapping, not processing)

### MQTT Subscribe Connector

- [ ] **2.5** Implement `MqttSubscribeConnector` (NEW — no v1 equivalent):
  - Connect to MQTT broker, subscribe to configured topics
  - Parse payload: JSONPath mode + plain_text mode
  - JSONPath: extract `$.value`, `$.ts`, `$.quality`
  - Plain text: entire payload = value, current time = timestamp
  - `test_connection()` — connect, verify broker reachable
  - `read_tags()` — not poll-based, return latest received values from internal cache

### Connector API

- [ ] **2.6** `GET /api/connections` — list all connectors with status
- [ ] **2.7** `POST /api/connections` — create draft connector config
- [ ] **2.8** `GET /api/connections/{id}` — get connector detail + config
- [ ] **2.9** `PUT /api/connections/{id}` — update draft config
- [ ] **2.10** `POST /api/connections/{id}/validate` — validate draft, return errors
- [ ] **2.11** `POST /api/connections/{id}/test` — test connection, return TestResult
- [ ] **2.12** `POST /api/connections/{id}/apply` — promote draft → active, restart connector
- [ ] **2.13** `POST /api/connections/{id}/confirm` — confirm apply success
- [ ] **2.14** `POST /api/connections/{id}/rollback` — revert to previous version
- [ ] **2.15** `POST /api/connections/{id}/start` — start connector
- [ ] **2.16** `POST /api/connections/{id}/stop` — stop connector
- [ ] **2.17** `POST /api/connections/{id}/restart` — restart connector
- [ ] **2.18** `GET /api/connections/{id}/tags` — list tag mappings
- [ ] **2.19** `POST /api/connections/{id}/tags` — add/update tag mapping
- [ ] **2.20** `DELETE /api/connections/{id}/tags/{tag_id}` — remove tag mapping
- [ ] **2.21** `POST /api/connections/{id}/tags/import` — CSV import
- [ ] **2.22** `GET /api/connections/{id}/tags/export` — CSV export
- [ ] **2.23** `GET /api/connections/{id}/browse` — browse OPC UA address space (OPC UA only)

### Config Manager — Safe Apply

- [ ] **2.24** Implement draft/validate/test/apply/confirm/rollback in `ConfigManager`:
  - `save_draft(section, fragment)` — save to draft area
  - `validate_draft(section)` — schema + business rules
  - `test_draft(section, connector_id)` — call connector.test_connection()
  - `apply_draft(section)` — promote to active, create backup
  - `confirm_apply(section, success)` — archive or rollback
  - `rollback(section, backup_path)` — restore previous version

### Heartbeat

- [ ] **2.25** Add connector status to heartbeat v2 payload:
  ```json
  {
    "connectors": [
      {"connector_id": "opcua_01", "type": "opcua", "status": "connected", "signal_count": 12, "last_error": null}
    ]
  }
  ```

### Console UI

- [ ] **2.26** Create `connections.html` — connector list with status cards
- [ ] **2.27** Create connection wizard (multi-step form):
  - Step 1: Protocol selection (OPC UA / Modbus TCP / MQTT)
  - Step 2: Connection parameters form
  - Step 3: Validate → show errors/warnings
  - Step 4: Test Connection → show result
  - Step 5: Browse tags (OPC UA) or manual entry (Modbus/MQTT)
  - Step 6: Tag mapping table (source_ref → signal_id → processing_profile)
  - Step 7: Review & Apply
  - Step 8: Confirm — connector status → success or [Rollback]

### Tests

- [ ] **2.28** OPC UA connector tests (connect, browse, read, reconnect, timeout)
- [ ] **2.29** Modbus TCP connector tests (connect, read registers, decode float32, timeout)
- [ ] **2.30** MQTT subscribe tests (connect, subscribe, receive JSON, plain text)
- [ ] **2.31** Connector lifecycle tests (start/stop/restart/error states)
- [ ] **2.32** Safe apply flow tests (draft→validate→test→apply→confirm, rollback on failure)
- [ ] **2.33** Heartbeat includes connector status tests

## Files to Create

```
edge-v2/agent/connectors/
  __init__.py
  base.py
  registry.py
  opcua/
    __init__.py
    connector.py
    client.py
    mapper.py
  modbus/
    __init__.py
    connector.py
    client.py
    mapper.py
  mqtt/
    __init__.py
    connector.py
    client.py

edge-v2/agent/web/routes/
  connections.py

edge-v2/console/static/
  connections.html
  js/connections.js
```

## Files to Modify

- `edge-v2/agent/main.py` — wire ConnectorRegistry
- `edge-v2/agent/config/config.py` — add safe apply methods
- `edge-v2/agent/config/config.edge-v2.yaml` — add connectors section

## Acceptance Criteria

```text
✅ User can create OPC UA, Modbus TCP, and MQTT connectors via wizard
✅ Test connection returns clear success/failure with detail
✅ User can map at least 5 signals without editing YAML
✅ Safe apply: draft → validate → test → apply → confirm works
✅ Rollback on apply failure restores previous config
✅ Connector status is visible in heartbeat and local dashboard
✅ CSV import/export works for tag mappings
✅ Invalid config is rejected with clear error messages
✅ OPC UA browse returns discoverable tags (namespace-filtered)
```

## Red Flags

- Stop if: connector config changes are applied without validation
- Stop if: test_connection() succeeds but read_tags() fails silently
- Stop if: rollback doesn't restore previous working state
- Stop if: constitution violation (direct connector → raw PLC tag binding in UI)
