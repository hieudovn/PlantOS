"""HTTP Poll Connector — implements BaseConnector for REST API polling.

GET-only for safety. JSONPath extraction from response body.
Configurable URL, headers, poll interval.
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any

from agent.connectors.base import (
    BaseConnector, ConnectorStatus, RawReading, TagConfig, TestResult,
)

logger = logging.getLogger(__name__)

try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False


class HttpPollConnector(BaseConnector):
    """HTTP Poll connector — polls REST endpoint, parses JSON response.

    GET-only for MVP. JSONPath extraction of values from response body.
    """

    def __init__(self, connector_id: str, config: dict):
        super().__init__(connector_id, config)
        self.connector_type = "http_poll"
        conn = config.get("connection", {})
        self.url = conn.get("url", "http://localhost:8080/api/test/measurements")
        self.headers = conn.get("headers", {})
        self._interval = config.get("poll_interval_ms", 5000) / 1000
        tags_raw = config.get("tags", [])
        self.tags = [TagConfig(**t) if isinstance(t, dict) else t for t in tags_raw]
        self._json_paths: dict[str, str] = {}
        for t in self.tags:
            self._json_paths[t.signal_id] = t.source_ref  # source_ref used as JSONPath
        self._task: asyncio.Task | None = None
        self._last_success: datetime | None = None
        self._last_error: str | None = None
        self._last_error_at: datetime | None = None

    async def validate_config(self, config: dict) -> list[str]:
        errors = []
        conn = config.get("connection", {})
        url = conn.get("url", "")
        if not url:
            errors.append("Missing 'connection.url'")
        elif not url.startswith(("http://", "https://")):
            errors.append("Invalid URL format — must start with http:// or https://")
        return errors

    async def test_connection(self) -> TestResult:
        import time
        conn = self.config.get("connection", {})
        url = conn.get("url", "http://localhost:8080/api/test/measurements")
        headers = conn.get("headers", {})

        if not HAS_HTTPX:
            return TestResult(success=False, message="httpx library not available")

        start = time.monotonic()
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(url, headers=headers)
                elapsed = (time.monotonic() - start) * 1000
                if resp.status_code == 200:
                    # Try parsing as JSON
                    try:
                        resp.json()
                    except Exception:
                        return TestResult(success=False, message="Response is not valid JSON",
                                          latency_ms=round(elapsed, 1))
                    return TestResult(success=True, message=f"HTTP {resp.status_code} — endpoint reachable",
                                      latency_ms=round(elapsed, 1))
                return TestResult(success=False,
                                  message=f"HTTP {resp.status_code}: {resp.reason_phrase}",
                                  latency_ms=round(elapsed, 1))
        except Exception as e:
            elapsed = (time.monotonic() - start) * 1000
            return TestResult(success=False, message=f"Connection failed: {e}",
                              latency_ms=round(elapsed, 1))

    async def start(self):
        self._task = asyncio.create_task(self._poll_loop())

    async def stop(self):
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        self._running = False

    async def status(self) -> ConnectorStatus:
        return ConnectorStatus(
            connector_id=self.connector_id,
            type=self.connector_type,
            status="running" if self._running else "stopped",
            connected=True,
            signal_count=len(self.tags),
            last_success_at=self._last_success,
            last_error=self._last_error,
            last_error_at=self._last_error_at,
        )

    async def read_tags(self, tag_configs: list[TagConfig]) -> list[RawReading]:
        """Fetch from HTTP endpoint and parse values."""
        if not HAS_HTTPX:
            return []
        readings = []
        now = datetime.now(timezone.utc)
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(self.url, headers=self.headers)
                if resp.status_code != 200:
                    return []
                data = resp.json()
                for tag in tag_configs:
                    if not tag.enabled:
                        continue
                    value = self._extract_value(data, tag.source_ref)
                    if value is not None:
                        readings.append(RawReading(
                            source_ref=tag.source_ref,
                            signal_id=tag.signal_id,
                            raw_value=float(value),
                            timestamp=now,
                        ))
        except Exception as e:
            logger.warning("HTTP Poll read error: %s", e)
        return readings

    def _extract_value(self, data: Any, json_path: str) -> Any | None:
        """Extract value from JSON using dot-separated path."""
        parts = json_path.strip("$.").split(".")
        current = data
        for part in parts:
            if isinstance(current, dict):
                current = current.get(part)
            elif isinstance(current, list):
                try:
                    current = current[int(part)]
                except (ValueError, IndexError):
                    return None
            else:
                return None
        return current

    async def browse(self, path: str = "") -> list[dict[str, Any]]:
        return [
            {"node_id": "$.value", "name": "Root value", "has_children": False, "depth": 0},
            {"node_id": "$.pump101_flow", "name": "Field: pump101_flow", "has_children": False, "depth": 0},
        ]

    async def _poll_loop(self):
        self._running = True
        while self._running:
            try:
                readings = await self.read_tags(self.tags)
                if readings:
                    self._last_success = datetime.now(timezone.utc)
                await asyncio.sleep(self._interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self._last_error = str(e)
                self._last_error_at = datetime.now(timezone.utc)
                logger.warning("HTTP Poll error: %s", e)
                await asyncio.sleep(self._interval)
        self._running = False
