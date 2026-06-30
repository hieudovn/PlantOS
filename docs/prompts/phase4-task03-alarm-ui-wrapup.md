# Phase 4 — Task 4-03: Alarm UI + Notification + Cache Fix (Wrap-Up)

> **Designer:** DeepSeek V4 Pro | **Date:** 2026-06-30
> **Final task of Phase 4!**

## Context

Phase 4 wrap-up: enhance Alarm UI, fix rule cache, add notification endpoint, update README.

## Implementation Checklist

- [ ] MODIFY `backend/app/modules/alarms/service.py` — invalidate cache after CRUD
- [ ] CREATE `backend/app/modules/alarms/notify.py` — webhook notification
- [ ] MODIFY `backend/app/modules/alarms/router.py` — add notification config endpoint
- [ ] MODIFY `frontend/src/features/alarms/AlarmPage.tsx` — enhance with filters, ack, severity colors
- [ ] UPDATE `README.md` — Phase 4 features
- [ ] RUN `python -m pytest tests/ -v` — verify 44 tests

## Detailed Instructions

### 1. Cache Fix — `service.py`

In `AlarmRuleService.create_rule`, `update_rule`, `delete_rule`: tạo một `AlarmEvaluator` instance và gọi `_invalidate_cache()`. Hoặc đơn giản hơn: thêm `_invalidate_cache()` call trong mỗi CRUD method của service.

### 2. Notification — `alarms/notify.py`

```python
"""Notification dispatcher for alarm events."""

import logging
import httpx

logger = logging.getLogger(__name__)


class NotificationService:
    def __init__(self):
        self._webhooks: list[str] = []  # Configured webhook URLs

    def add_webhook(self, url: str):
        if url not in self._webhooks:
            self._webhooks.append(url)

    async def send_alarm_notification(self, alarm: dict):
        """Send alarm notification to all configured webhooks."""
        if not self._webhooks:
            return

        payload = {
            "type": "alarm",
            "alarm_id": alarm.get("alarm_id"),
            "severity": alarm.get("severity"),
            "state": alarm.get("state"),
            "message": alarm.get("message"),
            "signal_id": alarm.get("signal_id"),
            "trigger_value": alarm.get("trigger_value"),
        }

        async with httpx.AsyncClient(timeout=5) as client:
            for url in self._webhooks:
                try:
                    await client.post(url, json=payload)
                except Exception as e:
                    logger.warning(f"Webhook {url} failed: {e}")
```

Add POST `/api/v1/notifications/webhook` endpoint to register webhook URLs.

### 3. Alarm UI Enhancement — `AlarmPage.tsx`

Enhance existing page with:
- **Filter bar**: state (active/acknowledged/cleared), severity (low/medium/high/critical)
- **Acknowledge button**: PATCH `/api/v1/alarms/{id}/ack`
- **Severity colors**: critical=red bg, high=orange, medium=yellow, low=blue
- **Auto-refresh**: 10s polling
- **Count badge**: active alarm count in sidebar

### 4. README Update

```markdown
## Phase 4 Features

- **Alarm Rule Engine** — Threshold-based alarm rules, form-based editor
- **Alarm State Machine** — Active → Acknowledged → Cleared lifecycle
- **Calculated Signals** — Virtual signals via formula (e.g., power = V × I)
- **Notification Service** — Webhook dispatch for alarm events
```

## Files

| # | File | Action |
|---|------|--------|
| 1 | `backend/app/modules/alarms/service.py` | MODIFY — cache invalidation |
| 2 | `backend/app/modules/alarms/notify.py` | CREATE |
| 3 | `backend/app/modules/alarms/router.py` | MODIFY — webhook endpoint |
| 4 | `frontend/src/features/alarms/AlarmPage.tsx` | MODIFY — enhanced UI |
| 5 | `README.md` | MODIFY |
