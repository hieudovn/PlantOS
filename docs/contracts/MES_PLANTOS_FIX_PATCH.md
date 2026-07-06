# MES PlantOSAdapter — Fix Patch for Cross-Project Verification

> **For:** MES PM  
> **From:** PlantOS PM  
> **Date:** 2026-07-06  
> **Reference:** `docs/contracts/MES_PLANTOS_CROSS_VERIFICATION_REPORT.md`

---

## 🔴 P0 — Fix event_id Regex (T/Z Case)

**File:** `odoo/custom_addons/mes_core/services/plantos_adapter.py`  
**Line:** ~18

### Current (BROKEN):

```python
_EVENT_ID_RE = re.compile(
    r"^plantos-[a-z0-9_.-]+-\d{8}T\d{6}Z-[a-f0-9]{6}$"
)
```

### Why it fails:

PlantOS contract §5 specifies lowercase `t` and `z` in event_id timestamps:
```
plantos-hsp-101.flow_rate-20260706t120000z-a1b2c3
                          ^lowercase  ^lowercase
```

The adapter regex uses uppercase literal `T` and `Z`. With no `re.IGNORECASE` flag, lowercase `t`/`z` will not match.

### Fix — Option A (case-insensitive, preferred):

```python
_EVENT_ID_RE = re.compile(
    r"^plantos-[a-z0-9_.-]+-\d{8}[tT]\d{6}[zZ]-[a-f0-9]{6}$"
)
```

### Fix — Option B (match PlantOS contract exactly):

```python
_EVENT_ID_RE = re.compile(
    r"^plantos-[a-z0-9_.-]+-\d{8}t\d{6}z-[a-f0-9]{6}$"
)
```

> **Recommendation:** Option A — accepts both cases. PlantOS contract mandates lowercase, but accepting uppercase provides forward flexibility if timestamp formatting changes.

### Verification after fix:

```python
# Should ALL match:
"plantos-comp01-core.speed-20260706t080000z-a1b2c3"   # lowercase (PlantOS standard)
"plantos-comp01-core.speed-20260706T080000Z-a1b2c3"   # uppercase (forward compat)
"plantos-hsp-101.flow_rate-20260706t120000z-a1b2c3"   # PlantOS contract example
```

---

## 🟡 P1 — Fix Topic Route Documentation

### File 1: `tools/uns_config.yaml`

**Line:** ~76 (PlantOS signal UNS route description)

**Current:**
```yaml
  # Signal telemetry via UNS topic
  - topic: "plantos/+/+/+/+/+"
    action: "process_plantos_event"
    description: "PlantOS SignalValueUpdated / SignalQualityChanged via UNS topic"
```

**Fix:**
```yaml
  # Signal telemetry via UNS topic
  - topic: "plantos/+/+/+/+/+"
    action: "process_plantos_event"
    description: "PlantOS SignalValueUpdated via signal UNS topic"
```

**Line:** ~84 (PlantOS event topic route description)

**Current:**
```yaml
  # System events via event topic
  - topic: "plantos/events/+"
    action: "process_plantos_event"
    description: "PlantOS AssetStatusChanged / AlarmRaised / AlarmCleared / EdgeHeartbeatReceived"
```

**Fix:**
```yaml
  # System events via event topic
  - topic: "plantos/events/+"
    action: "process_plantos_event"
    description: "PlantOS AssetStatusChanged / AlarmRaised / AlarmCleared / SignalQualityChanged / EdgeHeartbeatReceived"
```

### File 2: `docs/status/MES_PLANTOS_FINAL_COMPLETION_REPORT.md`

**Section 5 — Data Flow Architecture table:**

SignalQualityChanged should be moved from the signal UNS row to the event topic row:

```markdown
| `plantos/{plant}/{area}/{asset}/{category}/{signal}` | SignalValueUpdated | 0 |
| `plantos/events/{event_type}` | AssetStatusChanged, AlarmRaised, AlarmCleared, SignalQualityChanged, EdgeHeartbeatReceived | 1 |
```

### File 3: SA Hardening §14 item #1

Update confirmation to reference `plantos/events/+` (event topic), not `plantos/+/+/+/+/+` (signal UNS).

---

## 🟡 P1 — Fix QoS Documentation

### File: `docs/status/MES_PLANTOS_FINAL_COMPLETION_REPORT.md`

**Section 5 table:**

| Current | Correct |
|---------|---------|
| SignalQualityChanged: QoS **0** (configurable 1) | SignalQualityChanged: QoS **1** |

Per PlantOS contract §6: `SignalQualityChanged | 1 | Data reliability`

---

## Verification Checklist

After applying fixes, verify:

```bash
# 1. Regex should accept both cases
python -c "
import re
r = re.compile(r'^plantos-[a-z0-9_.-]+-\d{8}[tT]\d{6}[zZ]-[a-f0-9]{6}$')
assert r.match('plantos-comp01-core.speed-20260706t080000z-a1b2c3')  # lowercase
assert r.match('plantos-comp01-core.speed-20260706T080000Z-a1b2c3')  # uppercase
print('✅ Regex fix verified')
"

# 2. Re-run integration tests
python tools/test_plantos_integration.py
# Expected: 8/8 passed (now through full adapter validation)

# 3. Verify uns_config.yaml comments
grep -A2 "plantos/+/+/+/+/+" tools/uns_config.yaml
grep -A2 "plantos/events/+" tools/uns_config.yaml
```
