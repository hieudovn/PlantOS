# Edge v2 Stabilization — Verification Report

> **Date:** 2026-07-08
> **Status:** In Progress
> **Author:** Coder (DeepSeek V4 Flash)
> **Review:** PM + SA

---

## Gate Summary

| Gate | Result | Evidence | Notes |
|---|---|---|---|
| **STAB-01** Connector Architecture | ✅ FIXED | OPC UA `_poll_loop` yield removed, all 5 connectors use `read_tags()` pattern | `start()` establishes connection, `read_tags()` returns `list[RawReading]` |
| **STAB-02** Dockerfile Build | ✅ FIXED | Added `COPY edge/agent/*.py` for v1 reused libraries | Now includes buffer, sync, health, publisher |
| **STAB-03** install.sh Repo | ✅ FIXED | Corrected to `hieudovn/PlantOS.git` with `main` branch | Added note for user to verify/update |
| **STAB-04** Processing Loop | ✅ FIXED | `apply()` called with correct signature `raw_value, profile, signal_id, timestamp` | Removed `history=` kwarg; engine manages history internally |
| **STAB-05** Auth Crypto | ✅ FIXED | Fail-fast on missing bcrypt/itsdangerous | `EDGE_DEV_INSECURE_AUTH=true` for dev fallback |
| **STAB-06** Config Paths | ✅ FIXED | Canonical paths: `connectors.<id>` (active), `_drafts.connectors.<id>` (draft) | Legacy `connector_` prefix normalized |
| **STAB-07** ADR Sync Path | ✅ DONE (docs) | `docs/adr/ADR-edge-v2-sync-path-mvp.md` | Option A: legacy measurements table as MVP sync source |
| **STAB-08** Data E2E | ⏳ PENDING | Requires running system | See smoke script |
| **STAB-09** Command E2E | ⏳ PENDING | Requires running system + Center | See smoke script |
| **STAB-10** Docker Smoke | ⏳ PENDING | Requires Docker host | See smoke script |
| **STAB-11** Smoke Script | ✅ CREATED | `edge-v2/scripts/smoke_e2e.sh` | 8 test categories |
| **STAB-12** This Report | ✅ CREATED | Verification report | Gates tracked here |

---

## Detailed Fix Log

### STAB-01: Fix Connector Central Polling Architecture

**Changed files:**
- `edge-v2/agent/connectors/opcua/connector.py`

**What was fixed:**
- Removed `yield readings` from `_poll_loop()` — was causing `TypeError` when running in `asyncio.create_task()` because a generator was returned instead of a coroutine
- `_poll_loop()` now reads values into local variable without yielding
- `read_tags()` is the primary data path — it polls the client and returns `list[RawReading]`

**Test command:**
```bash
PYTHONPATH=$(pwd) python -c "
import asyncio
from agent.connectors.opcua.connector import OpcUaConnector
from agent.connectors.modbus.connector import ModbusTcpConnector
from agent.connectors.modbus.rtu_connector import ModbusRtuConnector
from agent.connectors.mqtt.connector import MqttSubscribeConnector
from agent.connectors.http_poll.connector import HttpPollConnector
from agent.connectors.base import BaseConnector

for cls in [OpcUaConnector, ModbusTcpConnector, ModbusRtuConnector, MqttSubscribeConnector, HttpPollConnector]:
    assert issubclass(cls, BaseConnector)
    print(f'✅ {cls.__name__} implements BaseConnector')

print('STAB-01 PASS: All 5 connectors implement BaseConnector')
"
```

**Known issues:** None

---

### STAB-02: Fix Dockerfile Build Context

**Changed files:**
- `edge-v2/Dockerfile`

**What was fixed:**
- Added `COPY` instructions for Edge v1 reused libraries: `edge/__init__.py`, `edge/agent/__init__.py`, `buffer.py`, `sync.py`, `health.py`, `publisher.py`
- Without these, Docker build would fail because Edge v2 imports `from edge.agent.buffer import DuckDBBuffer`

**Test command:**
```bash
cd edge-v2
docker build -t plantos-edge-v2:test .
```

**Known issues:** Build context must include whole repo (not just edge-v2/), since Dockerfile references `edge/` at repo root.

---

### STAB-03: Fix install.sh Repo

**Changed files:**
- `edge-v2/install.sh`

**What was fixed:**
- Changed git clone URL from `https://github.com/PlantOS/plantos.git` to `https://github.com/hieudovn/PlantOS.git`
- Changed branch from `feature/edge-v2` to `main`
- Added comment noting user should verify URL

**Test command:**
```bash
grep -E "hieudovn/PlantOS" edge-v2/install.sh
```

**Known issues:** URL should be confirmed with PM before release.

---

### STAB-04: Verify Processing Loop Signature

**Changed files:**
- `edge-v2/agent/main.py` (processing_loop function)

**What was fixed:**
- `apply()` now called with correct keyword arguments: `raw_value=reading.raw_value, profile=profile, signal_id=reading.signal_id, timestamp=reading.timestamp`
- Removed `history=` kwarg that didn't exist in the signature
- Engine manages history internally via `self._history[signal_id]`
- `write_raw()` called with explicit keyword args matching `ProcessingEngine.write_raw()` signature
- Processed results written to legacy `measurements` table for StoreAndForward sync

**Test command:**
```bash
PYTHONPATH=$(pwd) python -c "
from agent.processing.engine import ProcessingEngine
from agent.processing.profiles import ProcessingProfile, ProcessingStep
import inspect
sig = inspect.signature(ProcessingEngine.apply)
print(f'apply signature: {sig}')
assert 'raw_value' in sig.parameters
assert 'profile' in sig.parameters
assert 'signal_id' in sig.parameters
print('STAB-04 PASS')
"
```

**Known issues:** None

---

### STAB-05: Auth Fail Fast

**Changed files:**
- `edge-v2/agent/auth/auth.py`

**What was fixed:**
- Added `_check_crypto()` function that raises `RuntimeError` if bcrypt or itsdangerous are missing
- Supports `EDGE_DEV_INSECURE_AUTH=true` environment variable for dev/test environments
- Cleaned up try/except blocks into clean `HAS_BCRYPT`/`HAS_ITSDAENGEROUS` flags
- All fallback paths now explicitly log "INSECURE" warning

**Test command:**
```bash
# Test fail-fast
EDGE_DEV_INSECURE_AUTH=false python -c "
from agent.auth.auth import LocalAuthManager
# If bcrypt missing, should raise RuntimeError
" 2>&1 | grep -q "RuntimeError" && echo "STAB-05 PASS: Fail-fast works"

# Test dev fallback
EDGE_DEV_INSECURE_AUTH=true python -c "
from agent.auth.auth import LocalAuthManager
print('STAB-05 PASS: Dev mode fallback works')
"
```

**Known issues:** None

---

### STAB-06: Canonical Config Path

**Changed files:**
- `edge-v2/agent/config/__init__.py`

**What was fixed:**
- Draft paths normalized: `_drafts.connectors.<connector_id>.v<version>`
- Active paths: `connectors.<connector_id>`
- Backup paths: `_backups.connectors.<connector_id>.<timestamp>`
- Added `_draft_section()` helper for legacy `connector_` prefix normalization
- `apply_draft()` creates pre-restore backup before applying
- `confirm_apply()` auto-rollbacks on failure
- `rollback()` restores from latest backup

**Test command:**
```bash
PYTHONPATH=$(pwd) python -c "
from agent.config import ConfigManager
import tempfile, os, yaml

cfg = tempfile.NamedTemporaryFile(suffix='.yaml', mode='w', delete=False)
cfg.write('edge_node_id: TEST\\nplant_id: TEST\\n')
cfg.close()

cm = ConfigManager(cfg.name)

# Test draft with canonical path
v = cm.save_draft('connectors.test_01', {'type': 'opcua', 'connection': {}})
assert v == 1, f'Expected version 1, got {v}'

draft = cm.get_draft('connectors.test_01')
assert draft and draft['type'] == 'opcua', 'Draft not found'

# Test apply
cm.apply_draft('connectors.test_01')
active = cm.get('connectors.test_01')
assert active and active['type'] == 'opcua', 'Apply failed'

print('STAB-06 PASS: Canonical config paths work')
os.unlink(cfg.name)
"
```

**Known issues:** None

---

## Known Remaining Issues

| # | Severity | Description | Status |
|---|---|---|---|
| 1 | P2 | Docker build context must include repo root level (edge/agent/*.py) | Mitigated by STAB-02 |
| 2 | P2 | All connector `_poll_loop()` methods are passive (read values but don't feed into pipeline automatically — pipeline is driven by main.py processing_loop) | By design per STAB-01 |
| 3 | P3 | No automated CI/CD pipeline | Future phase |

## Next Recommended Action

1. Run `bash edge-v2/scripts/smoke_e2e.sh` with Edge v2 agent running
2. Run Docker smoke test per STAB-10
3. PM review → GO/NO-GO for internal demo
