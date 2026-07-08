# E2V2-6: Protocol Expansion (Modbus RTU + HTTP Poll)

## Context

After the internal demo milestone, add Modbus RTU (serial) and HTTP/REST polling connectors. Siemens S7 is explicitly POST-MVP — do NOT implement in this phase.

## Plan Reference

- `docs/phase-edge-v2-productization-plan.md` §9.1, §3.3
- `docs/01-project-constitution.md`
- `docs/60-edge-center-strategy.md`

## Constitution Checklist

- [x] New connectors follow BaseConnector interface
- [x] Connectors use signal_id mapping, not raw protocol identifiers
- [x] Safe apply/rollback applies to all connectors
- [x] No PLC write or control
- [x] S7 explicitly excluded from this phase

## Implementation Checklist

### Modbus RTU Connector

- [ ] **6.1** Implement `ModbusRtuConnector(BaseConnector)`:
  - Serial port connection (e.g., `/dev/ttyUSB0`, `COM3`)
  - Baud rate, parity, stop bits, data bits configurable
  - Same register mapping as Modbus TCP (holding, coil, input, discrete)
  - Same data type decoding (float32, int16, uint32)
  - `test_connection()` — open serial port, read known register
  - `validate_config()` — check serial port format, register ranges
  - `read_tags()` — batch read by register type

- [ ] **6.2** Create Modbus RTU connection wizard:
  - Serial port selection (with platform-aware defaults)
  - Baud rate: 9600, 19200, 38400, 115200
  - Parity: None, Even, Odd
  - Test connection → read known register

### HTTP Poll Connector

- [ ] **6.3** Implement `HttpPollConnector(BaseConnector)`:
  - Configurable URL, method (GET only for MVP), headers
  - Poll interval configurable
  - Response parsing: JSONPath to extract value from response body
  - `test_connection()` — make GET request, check 2xx response
  - `validate_config()` — check URL format, required headers
  - `read_tags()` — make request, parse response, map to signals

- [ ] **6.4** Create HTTP Poll connection wizard:
  - URL input
  - Custom headers (key-value pairs)
  - Poll interval
  - JSONPath expression for value extraction
  - Test connection → show parsed sample value

### Simulator

- [ ] **6.5** Add Modbus RTU simulator to `edge-v2/simulator/protocol_servers/`:
  - Use `pymodbus` server in RTU mode
  - Serve 10 holding registers with test values
  - Configurable serial port (virtual serial pair for CI)

- [ ] **6.6** Add HTTP test endpoint to simulator:
  - Simple HTTP server returning JSON with test values
  - Endpoint: `/api/test/measurements` → `{"pump101_flow": 12.5, "tank101_level": 85.3}`

### Console

- [ ] **6.7** Add Modbus RTU to connection wizard protocol selector
- [ ] **6.8** Add HTTP Poll to connection wizard protocol selector

### Tests

- [ ] **6.9** Modbus RTU connector tests (connect, read registers, serial timeout)
- [ ] **6.10** HTTP Poll connector tests (connect, parse JSON, timeout, error handling)
- [ ] **6.11** Both new connectors integrate with safe apply/rollback flow

## Files to Create

```
edge-v2/agent/connectors/modbus/
  rtu_connector.py      # ModbusRtuConnector
  rtu_client.py

edge-v2/agent/connectors/http_poll/
  __init__.py
  connector.py

edge-v2/simulator/protocol_servers/
  modbus_rtu_server.py
  http_test_server.py
```

## Files to Modify

```
edge-v2/agent/connectors/registry.py — add modbus_rtu + http_poll
edge-v2/console/static/connections.html — add new protocol options
edge-v2/console/static/js/connections.js — add new wizard steps
```

## Acceptance Criteria

```text
✅ Modbus RTU connector reads from serial simulator
✅ HTTP Poll connector reads from REST endpoint
✅ Both connectors integrate with processing pipeline
✅ Both connectors have connection wizards
✅ Safe apply/rollback works for both
✅ Test connection returns clear results
✅ S7 connector is NOT implemented (post-MVP)
```

## Red Flags

- Stop if: Modbus RTU write operations are implemented (read-only only)
- Stop if: HTTP Poll supports POST/PUT/DELETE (GET only for safety)
- Stop if: any S7 code is written (explicitly post-MVP)
- Stop if: constitution violation (raw protocol access bypassing signal mapping)
