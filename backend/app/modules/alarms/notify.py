"""Notification dispatcher for alarm events."""

import logging
import httpx

logger = logging.getLogger(__name__)


class NotificationService:
    def __init__(self):
        self._webhooks: list[str] = []

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
