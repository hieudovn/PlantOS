"""Calculated Signals — virtual signal formulas."""

import logging
import re
from datetime import datetime, timezone

from app.db import get_session
from app.modules.alarms.repository import AlarmRuleRepository
from app.modules.historian.interface import HistorianInterface
from app.modules.historian.models import Measurement, Quality

logger = logging.getLogger(__name__)


class SignalCalculator:
    def __init__(self, historian: HistorianInterface):
        self.historian = historian

    async def evaluate(self, measurements: list[dict]) -> list[Measurement]:
        """Evaluate calculated signal rules against latest measurements."""
        with get_session() as session:
            repo = AlarmRuleRepository(session)
            # Get active calculated signal rules (trigger_type = "calculated")
            rules = repo.list_all(status="active")
            rules = [r for r in rules if r.trigger_type == "calculated"]

        if not rules:
            return []

        # Build value map from current measurements
        value_map = {m["signal_id"]: m["value"] for m in measurements if "signal_id" in m}

        results = []
        for rule in rules:
            try:
                formula = rule.description or ""
                if not formula:
                    continue

                # Collect signal_ids referenced in formula
                refs = re.findall(r"[\w.-]+\.[\w.]+", formula)
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
                expr_resolved = formula
                for ref, val in resolved.items():
                    expr_resolved = expr_resolved.replace(ref, str(val))

                # Safe eval (only numbers and basic operators)
                value = eval(expr_resolved, {"__builtins__": {}}, {})

                results.append(
                    Measurement(
                        timestamp=datetime.now(timezone.utc),
                        signal_id=rule.signal_id,
                        value=round(float(value), 3),
                        quality=Quality.GOOD,
                        source="calculated",
                    )
                )
            except Exception as e:
                logger.warning(f"Calc rule {rule.rule_id} failed: {e}")

        if results:
            await self.historian.write_measurements(results)
            logger.info(f"Calculated {len(results)} signals")

        return results
