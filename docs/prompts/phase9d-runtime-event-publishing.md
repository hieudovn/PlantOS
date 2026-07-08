# Phase 9D — Runtime Event Publishing Implementation

> **Phase:** 9D (MES Integration — Runtime)  
> **Depends on:** Phase 9A/9B/9C (contract spec, migration, UNS)  
> **Effort:** 4-5h  
> **Priority:** HIGH — unblocks MES C8 runtime adapter testing  
> **Contract:** `docs/contracts/PLANTOS_RUNTIME_EVENT_CONTRACT.md`

---

## Objective

Implement MQTT event publishing so MES can subscribe to real-time PlantOS events. When measurements are ingested, alarms fire, or edges heartbeat — PlantOS publishes structured MQTT events in the exact format defined by the Phase 9D runtime event contract.

---

## Architecture Overview

```
Measurement Ingest → dispatch("measurements.ingested")
                         ├── websocket broadcast (existing)
                         ├── alarm evaluator (existing)
                         ├── calc signal evaluator (existing)
                         ├── [NEW] SignalValueUpdated publisher
                         └── [NEW] SignalQualityChanged publisher

Alarm Evaluator → dispatch("alarm.raised") / dispatch("alarm.cleared")
                         ├── [NEW] AlarmRaised publisher
                         └── [NEW] AlarmCleared publisher

Edge Heartbeat → dispatch("edge.heartbeat")
                         └── [NEW] EdgeHeartbeatReceived publisher
```

All new publishers use the same MQTT client singleton → publish to EMQX → MES subscribes.

---

## Task 1: Add paho-mqtt Dependency

**File:** `backend/pyproject.toml`

Add to `dependencies`:
```toml
"paho-mqtt>=2.1.0",
```

---

## Task 2: Create MQTT Publisher Singleton

**New file:** `backend/app/modules/events/publisher.py`

Requirements:
- Singleton `MqttPublisher` class that manages a persistent `paho.mqtt.client.Client` connection to EMQX
- Connects at startup, reconnects automatically
- Publishes events asynchronously (fire-and-forget — failure logged but does not block caller)
- Maps event type to correct QoS per contract
- Maps event type to correct topic per contract

```python
"""MQTT event publisher — singleton client to EMQX."""

import json
import logging
import threading
import time
from dataclasses import dataclass

import paho.mqtt.client as mqtt

from app.core.config import settings

logger = logging.getLogger(__name__)

# QoS mapping per contract §6
EVENT_QOS: dict[str, int] = {
    "SignalValueUpdated": 0,
    "AssetStatusChanged": 1,
    "AlarmRaised": 1,
    "AlarmCleared": 1,
    "SignalQualityChanged": 1,
    "EdgeHeartbeatReceived": 0,
}

# Topic mapping per contract §1
def get_event_topic(event_type: str, uns_topic: str | None = None) -> str:
    """Return the MQTT topic for an event type.
    
    SignalValueUpdated uses the signal UNS topic.
    All other types use plantos/events/{event_type}.
    """
    if event_type == "SignalValueUpdated" and uns_topic:
        return uns_topic
    return f"plantos/events/{event_type}"


class MqttPublisher:
    """Singleton MQTT publisher for runtime events."""
    
    _instance: "MqttPublisher | None" = None
    _lock = threading.Lock()
    
    def __init__(self):
        self._client = mqtt.Client(client_id="plantos-center-events", clean_session=True)
        self._client.on_connect = self._on_connect
        self._client.on_disconnect = self._on_disconnect
        self._connected = False
        self._started = False
    
    @classmethod
    def get_instance(cls) -> "MqttPublisher":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance
    
    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self._connected = True
            logger.info("MQTT publisher connected to EMQX at %s:%s", settings.EMQX_HOST, settings.EMQX_MQTT_PORT)
        else:
            logger.warning("MQTT publisher connection failed, rc=%s", rc)
    
    def _on_disconnect(self, client, userdata, rc):
        self._connected = False
        if rc != 0:
            logger.warning("MQTT publisher disconnected unexpectedly, rc=%s", rc)
    
    def start(self):
        """Connect to EMQX and start the MQTT loop in a background thread."""
        if self._started:
            return
        try:
            self._client.connect(settings.EMQX_HOST, settings.EMQX_MQTT_PORT, keepalive=60)
            self._client.loop_start()
            self._started = True
            logger.info("MQTT publisher loop started")
        except Exception:
            logger.exception("Failed to start MQTT publisher — events will not be published")
    
    def stop(self):
        """Disconnect and stop the MQTT loop."""
        if self._started:
            self._client.loop_stop()
            self._client.disconnect()
            self._started = False
            logger.info("MQTT publisher stopped")
    
    def publish(self, event_type: str, payload: dict, uns_topic: str | None = None):
        """Publish an event to MQTT.
        
        Fire-and-forget: logs errors but does not raise.
        """
        try:
            topic = get_event_topic(event_type, uns_topic)
            qos = EVENT_QOS.get(event_type, 0)
            payload_str = json.dumps(payload, default=str)
            result = self._client.publish(topic, payload_str, qos=qos)
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.debug("Published %s to %s (qos=%s)", event_type, topic, qos)
            else:
                logger.warning("MQTT publish failed for %s: rc=%s", event_type, result.rc)
        except Exception:
            logger.exception("MQTT publish error for %s", event_type)
```

---

## Task 3: Create Event Builders

**New file:** `backend/app/modules/events/builders.py`

Functions that build the complete event envelope per contract for each of the 6 event types.

```python
"""Event envelope builders — produce contract-compliant MQTT payloads."""

import secrets
from datetime import datetime, timezone

from app.modules.signals.uns import build_uns_topic


def _make_event_id(entity_id: str, timestamp: datetime | None = None) -> str:
    """Generate event_id per contract §5.
    
    Format: plantos-{entity_id_lower}-{YYYYMMDDTHHMMSSZ}-{random6}
    """
    ts = (timestamp or datetime.now(timezone.utc)).strftime("%Y%m%dt%H%M%Sz")
    random6 = secrets.token_hex(3)  # 6 hex chars
    return f"plantos-{entity_id.lower()}-{ts}-{random6}"


def _make_correlation_id(entity_type: str, asset_id: str, instance_key: str, timestamp: datetime | None = None) -> str:
    """Generate correlation_id for alarm pairs per contract §7.
    
    Format: alarm-{asset_id}-{alarm_code}-{ISO8601}
    """
    ts = (timestamp or datetime.now(timezone.utc)).strftime("%Y%m%dT%H%M%SZ")
    return f"{entity_type}-{asset_id}-{instance_key}-{ts}"


def build_signal_value_updated(measurement: dict, signal_info: dict, asset_info: dict) -> dict:
    """Build SignalValueUpdated event per contract §4.1."""
    now = datetime.now(timezone.utc)
    signal_id = measurement["signal_id"]
    uns_topic = build_uns_topic(
        plant_id=asset_info["plant_id"],
        area_id=asset_info["area_id"],
        asset_id=asset_info["asset_id"],
        signal_category=signal_info.get("signal_category", "measurement"),
        signal_name=signal_info.get("signal_name", signal_id.split(".")[-1] if "." in signal_id else signal_id),
    )
    return {
        "schema_version": "1.0",
        "source_system": "plantos_center",
        "event_id": _make_event_id(signal_id, now),
        "correlation_id": None,
        "event_type": "SignalValueUpdated",
        "timestamp": now.isoformat(),
        "asset": {
            "plant_id": asset_info["plant_id"],
            "area_id": asset_info["area_id"],
            "asset_id": asset_info["asset_id"],
            "asset_code": asset_info.get("asset_code", ""),
            "asset_type": asset_info.get("asset_type", ""),
            "asset_role": asset_info.get("asset_role", ""),
        },
        "signal": {
            "signal_id": signal_id,
            "signal_name": signal_info.get("signal_name", ""),
            "signal_category": signal_info.get("signal_category", "measurement"),
            "data_type": signal_info.get("data_type", "float"),
            "engineering_unit": signal_info.get("engineering_unit", ""),
        },
        "edge": None,
        "alarm": None,
        "uns_topic": uns_topic,
        "payload": {
            "value": measurement["value"],
            "quality": measurement.get("quality", "GOOD"),
        },
    }


def build_signal_quality_changed(signal_id: str, quality: str, previous_quality: str,
                                  signal_info: dict, asset_info: dict, reason: str = "") -> dict:
    """Build SignalQualityChanged event per contract §4.5."""
    now = datetime.now(timezone.utc)
    return {
        "schema_version": "1.0",
        "source_system": "plantos_center",
        "event_id": _make_event_id(f"{signal_id}.quality", now),
        "correlation_id": None,
        "event_type": "SignalQualityChanged",
        "timestamp": now.isoformat(),
        "asset": {
            "plant_id": asset_info["plant_id"],
            "area_id": asset_info["area_id"],
            "asset_id": asset_info["asset_id"],
            "asset_code": asset_info.get("asset_code", ""),
            "asset_type": asset_info.get("asset_type", ""),
            "asset_role": asset_info.get("asset_role", ""),
        },
        "signal": {
            "signal_id": signal_id,
            "signal_name": signal_info.get("signal_name", ""),
            "signal_category": signal_info.get("signal_category", "measurement"),
        },
        "edge": None,
        "alarm": None,
        "uns_topic": f"plantos/events/SignalQualityChanged",
        "payload": {
            "quality": quality,
            "previous_quality": previous_quality,
            "reason": reason,
        },
    }


def build_alarm_raised(alarm_event: dict, rule_info: dict, asset_info: dict) -> dict:
    """Build AlarmRaised event per contract §4.3."""
    now = datetime.now(timezone.utc)
    alarm_code = rule_info.get("alarm_code", rule_info.get("name", "UNKNOWN"))
    return {
        "schema_version": "1.0",
        "source_system": "plantos_center",
        "event_id": _make_event_id(f"alarm.{alarm_event['alarm_id']}", now),
        "correlation_id": _make_correlation_id("alarm", asset_info["asset_id"], alarm_code, now),
        "event_type": "AlarmRaised",
        "timestamp": now.isoformat(),
        "asset": {
            "plant_id": asset_info["plant_id"],
            "area_id": asset_info["area_id"],
            "asset_id": asset_info["asset_id"],
            "asset_code": asset_info.get("asset_code", ""),
            "asset_type": asset_info.get("asset_type", ""),
            "asset_role": asset_info.get("asset_role", ""),
        },
        "signal": None,
        "edge": None,
        "alarm": {
            "alarm_code": alarm_code,
            "severity": rule_info.get("severity", "warning"),
            "description": alarm_event.get("message", ""),
            "state": "raised",
            "threshold_value": rule_info.get("threshold"),
            "actual_value": alarm_event.get("trigger_value"),
        },
        "uns_topic": "plantos/events/AlarmRaised",
        "payload": {},
    }


def build_alarm_cleared(alarm_event: dict, rule_info: dict, asset_info: dict, correlation_id: str) -> dict:
    """Build AlarmCleared event per contract §4.4."""
    now = datetime.now(timezone.utc)
    alarm_code = rule_info.get("alarm_code", rule_info.get("name", "UNKNOWN"))
    return {
        "schema_version": "1.0",
        "source_system": "plantos_center",
        "event_id": _make_event_id(f"alarm.{alarm_event['alarm_id']}.cleared", now),
        "correlation_id": correlation_id,
        "event_type": "AlarmCleared",
        "timestamp": now.isoformat(),
        "asset": {
            "plant_id": asset_info["plant_id"],
            "area_id": asset_info["area_id"],
            "asset_id": asset_info["asset_id"],
            "asset_code": asset_info.get("asset_code", ""),
            "asset_type": asset_info.get("asset_type", ""),
            "asset_role": asset_info.get("asset_role", ""),
        },
        "signal": None,
        "edge": None,
        "alarm": {
            "alarm_code": alarm_code,
            "severity": rule_info.get("severity", "warning"),
            "state": "cleared",
            "cleared_by": "auto",
        },
        "uns_topic": "plantos/events/AlarmCleared",
        "payload": {},
    }


def build_edge_heartbeat(edge_data: dict) -> dict:
    """Build EdgeHeartbeatReceived event per contract §4.6."""
    now = datetime.now(timezone.utc)
    return {
        "schema_version": "1.0",
        "source_system": "plantos_center",
        "event_id": _make_event_id(f"edge.{edge_data['edge_node_id']}.heartbeat", now),
        "correlation_id": None,
        "event_type": "EdgeHeartbeatReceived",
        "timestamp": now.isoformat(),
        "asset": None,
        "signal": None,
        "edge": {
            "edge_id": edge_data["edge_node_id"],
            "status": edge_data.get("status", "online"),
            "ip_address": edge_data.get("ip_address", ""),
            "signal_count": edge_data.get("signal_count", 0),
            "version": edge_data.get("version", ""),
        },
        "alarm": None,
        "uns_topic": "plantos/events/EdgeHeartbeatReceived",
        "payload": {},
    }


def build_asset_status_changed(asset_id: str, status: str, previous_status: str,
                                asset_info: dict, reason: str = "") -> dict:
    """Build AssetStatusChanged event per contract §4.2."""
    now = datetime.now(timezone.utc)
    return {
        "schema_version": "1.0",
        "source_system": "plantos_center",
        "event_id": _make_event_id(f"asset.{asset_id}.status", now),
        "correlation_id": None,
        "event_type": "AssetStatusChanged",
        "timestamp": now.isoformat(),
        "asset": {
            "plant_id": asset_info["plant_id"],
            "area_id": asset_info["area_id"],
            "asset_id": asset_info["asset_id"],
            "asset_code": asset_info.get("asset_code", ""),
            "asset_type": asset_info.get("asset_type", ""),
            "asset_role": asset_info.get("asset_role", ""),
        },
        "signal": None,
        "edge": None,
        "alarm": None,
        "uns_topic": "plantos/events/AssetStatusChanged",
        "payload": {
            "status": status,
            "previous_status": previous_status,
            "reason": reason,
        },
    }
```

---

## Task 4: Create Signal+Asset Info Resolver

**New file:** `backend/app/modules/events/resolver.py`

The builders need `signal_info` and `asset_info` dicts. Create a helper that resolves these from PostgreSQL.

```python
"""Resolve signal and asset metadata for event building."""

import logging
from functools import lru_cache

from app.db import get_session
from app.modules.assets.repository import AssetRepository
from app.modules.signals.repository import SignalRepository

logger = logging.getLogger(__name__)

# Cache asset/signal info for 5 minutes to avoid DB hits on every measurement
_CACHE_TTL = 300  # seconds


def resolve_signal_info(signal_id: str) -> dict | None:
    """Get signal metadata needed for event envelopes."""
    try:
        with get_session() as session:
            repo = SignalRepository(session)
            signal = repo.get_by_id(signal_id)
            if not signal:
                logger.warning("Signal not found for event: %s", signal_id)
                return None
            return {
                "signal_id": signal.signal_id,
                "signal_name": signal.signal_name,
                "signal_category": getattr(signal, "signal_category", "measurement"),
                "data_type": getattr(signal, "data_type", "float"),
                "engineering_unit": getattr(signal, "engineering_unit", ""),
                "asset_id": signal.asset_id,
            }
    except Exception:
        logger.exception("Failed to resolve signal info for %s", signal_id)
        return None


def resolve_asset_info(asset_id: str) -> dict | None:
    """Get asset metadata needed for event envelopes."""
    try:
        with get_session() as session:
            repo = AssetRepository(session)
            asset = repo.get_by_id(asset_id)
            if not asset:
                logger.warning("Asset not found for event: %s", asset_id)
                return None
            return {
                "asset_id": asset.asset_id,
                "asset_code": getattr(asset, "asset_code", ""),
                "asset_type": getattr(asset, "asset_type", ""),
                "asset_role": getattr(asset, "asset_role", ""),
                "plant_id": asset.plant_id,
                "area_id": asset.area_id,
            }
    except Exception:
        logger.exception("Failed to resolve asset info for %s", asset_id)
        return None
```

---

## Task 5: Create Event Publishing Subscribers

**New file:** `backend/app/modules/events/subscribers.py`

Register with EventDispatcher. These are the bridge between internal events and MQTT publishing.

```python
"""Event publishing subscribers — bridge internal EventDispatcher to MQTT."""

import logging

from app.modules.events.publisher import MqttPublisher
from app.modules.events.builders import (
    build_signal_value_updated,
    build_signal_quality_changed,
    build_alarm_raised,
    build_alarm_cleared,
    build_edge_heartbeat,
)
from app.modules.events.resolver import resolve_signal_info, resolve_asset_info

logger = logging.getLogger(__name__)

# Track previous quality per signal for change detection
_previous_quality: dict[str, str] = {}


async def on_measurements_ingested(data: dict):
    """Publish SignalValueUpdated events for each ingested measurement."""
    measurements = data.get("measurements", [])
    if not measurements:
        return
    
    publisher = MqttPublisher.get_instance()
    
    for m in measurements:
        try:
            signal_id = m.get("signal_id", "")
            if not signal_id:
                continue
            
            # Resolve metadata
            signal_info = resolve_signal_info(signal_id)
            if not signal_info:
                continue
            
            asset_info = resolve_asset_info(signal_info["asset_id"])
            if not asset_info:
                continue
            
            # Build and publish SignalValueUpdated
            event = build_signal_value_updated(m, signal_info, asset_info)
            publisher.publish("SignalValueUpdated", event, uns_topic=event["uns_topic"])
            
            # Check for quality change
            quality = m.get("quality", "GOOD")
            prev = _previous_quality.get(signal_id)
            if prev and prev != quality:
                q_event = build_signal_quality_changed(
                    signal_id, quality, prev, signal_info, asset_info,
                    reason=f"Quality changed from {prev} to {quality}"
                )
                publisher.publish("SignalQualityChanged", q_event)
            _previous_quality[signal_id] = quality
            
        except Exception:
            logger.exception("Failed to publish event for measurement %s", m.get("signal_id", "?"))


async def on_alarm_raised(data: dict):
    """Publish AlarmRaised event."""
    publisher = MqttPublisher.get_instance()
    try:
        alarm_event = data.get("alarm", {})
        rule_info = data.get("rule", {})
        asset_id = alarm_event.get("asset_id") or rule_info.get("asset_id", "")
        
        asset_info = resolve_asset_info(asset_id)
        if not asset_info:
            logger.warning("Cannot publish AlarmRaised: asset %s not found", asset_id)
            return
        
        event = build_alarm_raised(alarm_event, rule_info, asset_info)
        publisher.publish("AlarmRaised", event)
    except Exception:
        logger.exception("Failed to publish AlarmRaised event")


async def on_alarm_cleared(data: dict):
    """Publish AlarmCleared event."""
    publisher = MqttPublisher.get_instance()
    try:
        alarm_event = data.get("alarm", {})
        rule_info = data.get("rule", {})
        correlation_id = data.get("correlation_id", "")
        asset_id = alarm_event.get("asset_id") or rule_info.get("asset_id", "")
        
        asset_info = resolve_asset_info(asset_id)
        if not asset_info:
            logger.warning("Cannot publish AlarmCleared: asset %s not found", asset_id)
            return
        
        event = build_alarm_cleared(alarm_event, rule_info, asset_info, correlation_id)
        publisher.publish("AlarmCleared", event)
    except Exception:
        logger.exception("Failed to publish AlarmCleared event")


async def on_edge_heartbeat(data: dict):
    """Publish EdgeHeartbeatReceived event."""
    publisher = MqttPublisher.get_instance()
    try:
        edge_data = data.get("edge", {})
        event = build_edge_heartbeat(edge_data)
        publisher.publish("EdgeHeartbeatReceived", event)
    except Exception:
        logger.exception("Failed to publish EdgeHeartbeatReceived event")
```

---

## Task 6: Modify Alarm Evaluator to Dispatch Internal Events

**File:** `backend/app/modules/alarms/service.py`

In the `AlarmEvaluator.evaluate()` method, after creating a new alarm (line ~140), add a dispatch call:

```python
# Inside evaluate(), after event_repo.create(event):
from app.core.events import dispatch

# Resolve rule info for event publishing
rule_data = {
    "name": rule.name,
    "alarm_code": getattr(rule, "alarm_code", rule.name),
    "severity": rule.severity,
    "threshold": rule.threshold,
    "condition": rule.condition,
}

alarm_data = {
    "alarm_id": alarm_id,
    "asset_id": rule.asset_id,
    "signal_id": signal_id,
    "severity": rule.severity,
    "state": "active",
    "message": message,
    "trigger_value": value,
}

await dispatch("alarm.raised", {"alarm": alarm_data, "rule": rule_data})
```

After clearing an alarm (line ~148, inside `event_repo.update(...)`), add:

```python
# After event_repo.update(...) for cleared alarm:
from app.core.events import dispatch

correlation_id = f"alarm-{rule.asset_id}-{getattr(rule, 'alarm_code', rule.name)}-{a.created_at.strftime('%Y%m%dT%H%M%SZ')}"

alarm_data = {
    "alarm_id": a.alarm_id,
    "asset_id": rule.asset_id,
    "signal_id": signal_id,
    "severity": rule.severity,
    "state": "cleared",
}

rule_data = {
    "name": rule.name,
    "alarm_code": getattr(rule, "alarm_code", rule.name),
    "severity": rule.severity,
}

await dispatch("alarm.cleared", {"alarm": alarm_data, "rule": rule_data, "correlation_id": correlation_id})
```

---

## Task 7: Modify Edge Heartbeat to Dispatch Internal Event

**File:** `backend/app/modules/edge_nodes/router.py`

In `receive_heartbeat()`, after storing heartbeat data (line ~40), add:

```python
# After _edge_nodes[data.edge_node_id] = {...}
import asyncio
from app.core.events import dispatch

edge_data = {
    "edge_node_id": data.edge_node_id,
    "status": data.status,
    "ip_address": client_ip,
    "signal_count": data.signal_count,
    "version": data.version,
}

# Dispatch in background — heartbeat endpoint should not wait for MQTT publish
asyncio.create_task(dispatch("edge.heartbeat", {"edge": edge_data}))
```

Note: `receive_heartbeat()` is currently synchronous (not `async def`). Wrap in `asyncio.create_task` with `asyncio.get_event_loop()`.

Better approach — make it async:

```python
from fastapi import APIRouter, Request
from app.core.events import dispatch

# Change to async
@router.post("/edge-nodes/heartbeat")
async def receive_heartbeat(data: HeartbeatRequest, request: Request):
    # ... existing code ...
    
    # Dispatch event
    await dispatch("edge.heartbeat", {"edge": edge_data})
    
    return {"status": "ok"}
```

---

## Task 8: Register Event Subscribers in main.py

**File:** `backend/app/main.py`

In `_register_event_subscribers()`, add new subscribers:

```python
def _register_event_subscribers():
    # ... existing imports and subscribers ...
    
    # NEW: MQTT event publishing subscribers
    from app.modules.events.subscribers import (
        on_measurements_ingested,
        on_alarm_raised,
        on_alarm_cleared,
        on_edge_heartbeat,
    )
    
    subscribe("measurements.ingested", on_measurements_ingested)
    subscribe("alarm.raised", on_alarm_raised)
    subscribe("alarm.cleared", on_alarm_cleared)
    subscribe("edge.heartbeat", on_edge_heartbeat)
    
    logger.info("MQTT event publishing subscribers registered")
```

Also start the MQTT publisher at startup and stop at shutdown:

In `lifespan()`:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    settings.validate_config()
    get_engine()
    _register_event_subscribers()
    
    # Start MQTT publisher
    from app.modules.events.publisher import MqttPublisher
    MqttPublisher.get_instance().start()
    
    yield
    
    # Shutdown
    from app.modules.events.publisher import MqttPublisher
    MqttPublisher.get_instance().stop()
    dispose_engine()
```

---

## Task 9: Handle Missing event_id for StateEvent

**File:** `backend/app/modules/events/schemas.py`

If `StateEventCreate` doesn't have `alarm_code` needed by the contract, verify the `AlarmRule` model has it. If not, the builder should use `rule.name` as fallback.

---

## Validation

1. ✅ `python -c "from app.modules.events.publisher import MqttPublisher; print('import ok')"`
2. ✅ `python -c "from app.modules.events.builders import build_signal_value_updated; print('import ok')"`
3. ✅ `python -c "from app.modules.events.subscribers import on_measurements_ingested; print('import ok')"`
4. ✅ Start backend — check logs for "MQTT publisher connected to EMQX"
5. ✅ Send a measurement via `POST /api/v1/measurements/ingest` — check EMQX for `plantos/wtp-demo-01/.../measurement/...` topic
6. ✅ Trigger an alarm — check EMQX for `plantos/events/AlarmRaised`
7. ✅ Clear an alarm — check EMQX for `plantos/events/AlarmCleared`
8. ✅ Send edge heartbeat — check EMQX for `plantos/events/EdgeHeartbeatReceived`
9. ✅ Verify event_id format: `^plantos-[a-z0-9_.-]+-\d{8}t\d{6}z-[a-f0-9]{6}$`
10. ✅ Verify lowercase `t`/`z` in event_id (MES P0 fix)
11. ✅ Verify QoS: SignalValueUpdated=0, Alarm*=1, etc.
12. ✅ Kill EMQX → backend still works (logs warning, no crash)
