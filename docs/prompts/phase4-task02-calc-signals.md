# Phase 4 — Task 4-02: Calculated Signals + Simulator Fix (Gộp)

> **Designer:** DeepSeek V4 Pro | **Date:** 2026-06-30

## Context

1. **Calculated Signals**: Virtual signals from formula (e.g., FEEDER-01.power = FEEDER-01.voltage × FEEDER-01.current). Được evaluate sau mỗi measurement ingest → lưu vào historian như measurement thật.

2. **Simulator Fix**: `--scenario` flag không override được generators vì set sau `__init__`. Sửa để scenario override hoạt động.

## Implementation Checklist

- [ ] CREATE `backend/app/modules/alarms/calculator.py` — Formula evaluator
- [ ] MODIFY `backend/app/modules/alarms/schemas.py` — add CalcRule schema
- [ ] MODIFY `backend/app/modules/alarms/router.py` — CRUD calculated signal rules
- [ ] MODIFY `backend/app/modules/measurements/router.py` — trigger calculation after ingest
- [ ] FIX `edge/simulator/simulator.py` — scenario override trước khi tạo generators

## Detailed Instructions

### 1. `backend/app/modules/alarms/calculator.py`

```python
"""Calculated Signals — virtual signal formulas."""

import logging
from app.db import get_session
from app.modules.alarms.repository import AlarmRuleRepository
from app.modules.historian.interface import HistorianInterface
from app.modules.historian.models import Measurement, Quality
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class SignalCalculator:
    def __init__(self, historian: HistorianInterface):
        self.historian = historian

    async def evaluate(self, measurements: list[dict]) -> list[Measurement]:
        """Evaluate calculated signal rules against latest measurements."""
        with get_session() as session:
            repo = AlarmRuleRepository(session)
            # Get active calculated signal rules (trigger_type = "calculated")
            rules = repo.list_by_type("calculated")

        if not rules:
            return []

        # Build value map from current measurements
        value_map = {m["signal_id"]: m["value"] for m in measurements}

        results = []
        for rule in rules:
            try:
                # Simple formula: "signal_a * signal_b" or "signal_a + signal_b"
                formula = rule.description or ""
                if not formula:
                    continue

                # Parse formula: replace signal_ids with actual values
                expr = formula
                # Collect signal_ids referenced in formula
                import re
                refs = re.findall(r'[\w.-]+\.[\w.]+', formula)
                resolved = {}
                for ref in refs:
                    if ref in value_map:
                        resolved[ref] = value_map[ref]
                    else:
                        # Try to get from historian
                        latest = await self.historian.query_latest([ref])
                        if latest.get(ref):
                            resolved[ref] = latest[ref].value

                # Only evaluate if all refs resolved
                if len(resolved) != len(refs):
                    continue

                # Replace refs with values in expression
                expr_resolved = expr
                for ref, val in resolved.items():
                    expr_resolved = expr_resolved.replace(ref, str(val))

                # Safe eval (only numbers and basic operators)
                value = eval(expr_resolved, {"__builtins__": {}}, {})

                results.append(Measurement(
                    timestamp=datetime.now(timezone.utc),
                    signal_id=rule.signal_id,
                    value=round(float(value), 3),
                    quality=Quality.GOOD,
                    source="calculated",
                ))
            except Exception as e:
                logger.warning(f"Calc rule {rule.rule_id} failed: {e}")

        if results:
            await self.historian.write_measurements(results)
            logger.info(f"Calculated {len(results)} signals")

        return results
```

### 2. Schemas — Add CalcRule

```python
class CalcRuleCreate(BaseModel):
    rule_id: str
    name: str
    signal_id: str
    formula: str  # e.g., "FEEDER-01.voltage * FEEDER-01.current"
    interval_seconds: int = 10
```

### 3. Router — Add endpoints

```python
@router.post("/calc-rules", ...)
@router.get("/calc-rules", ...)
@router.delete("/calc-rules/{rule_id}", ...)
```

### 4. Trigger in measurements router

```python
from app.modules.alarms.calculator import SignalCalculator

# After ingest + alarm evaluation:
if result.accepted > 0:
    calc = SignalCalculator(historian)
    await calc.evaluate(ws_data)
```

### 5. Simulator Fix

Sửa `Simulator.__init__` để nhận `scenario` parameter:

```python
class Simulator:
    def __init__(self, config_path: str, scenario: str | None = None):
        # ... load config ...
        self.scenario = scenario or self.config.get("scenario", "normal_operation")
        # ... create generators WITH scenario applied ...
```

Và trong `__main__`:

```python
sim = Simulator(args.config, scenario=args.scenario)
# Remove: if args.scenario: sim.scenario = args.scenario  ← xóa dòng này
```

## Validation

```bash
# 1. Create calc rule: power = voltage × current
curl -X POST http://localhost:8000/api/v1/calc-rules -d '{
  "rule_id":"feeder-power","name":"Feeder Power",
  "signal_id":"FEEDER-01.calculated_power",
  "formula":"FEEDER-01.voltage * FEEDER-01.current"
}'

# 2. Run simulator
python simulator.py --duration 10

# 3. Check calculated signal
curl "http://localhost:8000/api/v1/measurements/current?signal_id=FEEDER-01.calculated_power"

# 4. Test scenario override (FIXED)
python simulator.py --scenario pump_high_pressure --duration 5
# Should print: "scenario=pump_high_pressure"
```

## Files

| # | File | Action |
|---|------|--------|
| 1 | `backend/app/modules/alarms/calculator.py` | CREATE |
| 2 | `backend/app/modules/alarms/schemas.py` | MODIFY |
| 3 | `backend/app/modules/alarms/router.py` | MODIFY |
| 4 | `backend/app/modules/measurements/router.py` | MODIFY |
| 5 | `edge/simulator/simulator.py` | FIX |
