# Phase 5 — Task 5-02: OPC UA Collector + Virtual Factory Integration

> **Designer:** DeepSeek V4 Pro | **Date:** 2026-06-30
> **Model:** Compressor Train Benchmark (flagship analytics plant)

## Context

Tích hợp Virtual Factory (D:\Project\Github\virtual-factory) vào PlantOS qua OPC UA,
dùng **Compressor Train Benchmark** — plant model mạnh nhất của VF với 25 industrial signals,
7 alarms, 6 sub-systems.

- Virtual Factory là **physics simulator** thuần túy — output OPC UA, không có CDM
- PlantOS Edge Agent đóng vai OPC UA Client — đọc, chuẩn hóa, ánh xạ signal_id
- PlantOS Center là **nơi duy nhất** đóng gói UNS/CDM
- KHÔNG dùng MQTT, HTTP, hay kênh nào khác giữa VF và PlantOS — chỉ OPC UA

## Compressor Train Plant Model

```
Boundary Source (GAS_SOURCE)
  │ suction line
  ▼
┌─────────────────────────────────────────────────────┐
│ COMP01 — Compressor Train A                          │
│                                                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐           │
│  │  MOTOR   │  │COMPRESSOR│  │BEARINGS  │           │
│  │ Current  │  │Suct Pres │  │DE Temp   │           │
│  │ Power    │  │Disch Pres│  │NDE Temp  │           │
│  │Wind Temp │  │Flow      │  │Thrust T  │           │
│  │Brg DE T  │  │Suct Temp │  │Vib DE    │           │
│  │Brg NDE T │  │Disch Temp│  │Vib NDE   │           │
│  │Vib DE    │  │Speed     │  │Vib Axial │           │
│  │Vib NDE   │  │Power     │  └──────────┘           │
│  └──────────┘  └──────────┘                         │
│                                                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐           │
│  │ LUBE OIL │  │ COOLING  │  │ SEAL GAS │           │
│  │ Pressure │  │Supply T  │  │Flow      │           │
│  │ Temp     │  │Return T  │  └──────────┘           │
│  │Filter DP │  └──────────┘                         │
│  └──────────┘                                       │
│                                                      │
│  ┌──────────────┐                                    │
│  │ ANTI-SURGE   │  (recycle valve, surge margin)    │
│  └──────────────┘                                    │
└─────────────────────────────────────────────────────┘
  │ discharge line
  ▼
Boundary Sink (GAS_SINK)
```

## Virtual Factory OPC UA Output (25 Signals)

Tất cả signal được OPC UA gateway publish với NodeId format `ns={idx};s={SIGNAL_NAME}`.

### Nhóm 1: Compressor Core (5 signals)

| OPC UA NodeId | Category | Unit | Type |
|---|---|---|---|
| `ns=2;s=COMP01_SUCTION_PRESSURE` | industrial_signal | kPa | float |
| `ns=2;s=COMP01_DISCHARGE_PRESSURE` | industrial_signal | kPa | float |
| `ns=2;s=COMP01_FLOW` | industrial_signal | m³/s | float |
| `ns=2;s=COMP01_SUCTION_TEMP` | industrial_signal | °C | float |
| `ns=2;s=COMP01_DISCHARGE_TEMP` | industrial_signal | °C | float |

### Nhóm 2: Motor (7 signals)

| OPC UA NodeId | Category | Unit | Type |
|---|---|---|---|
| `ns=2;s=COMP01_MOTOR_CURRENT` | industrial_signal | A | float |
| `ns=2;s=COMP01_MOTOR_POWER` | industrial_signal | kW | float |
| `ns=2;s=COMP01_MOTOR_WINDING_TEMP` | industrial_signal | °C | float |
| `ns=2;s=COMP01_MOTOR_BRG_DE_TEMP` | industrial_signal | °C | float |
| `ns=2;s=COMP01_MOTOR_BRG_NDE_TEMP` | industrial_signal | °C | float |
| `ns=2;s=COMP01_MOTOR_VIB_DE` | industrial_signal | mm/s | float |
| `ns=2;s=COMP01_MOTOR_VIB_NDE` | industrial_signal | mm/s | float |

### Nhóm 3: Compressor Bearings & Vibration (6 signals)

| OPC UA NodeId | Category | Unit | Type |
|---|---|---|---|
| `ns=2;s=COMP01_BRG_DE_TEMP` | industrial_signal | °C | float |
| `ns=2;s=COMP01_BRG_NDE_TEMP` | industrial_signal | °C | float |
| `ns=2;s=COMP01_BRG_THRUST_TEMP` | industrial_signal | °C | float |
| `ns=2;s=COMP01_VIB_DE` | industrial_signal | mm/s | float |
| `ns=2;s=COMP01_VIB_NDE` | industrial_signal | mm/s | float |
| `ns=2;s=COMP01_VIB_AXIAL` | industrial_signal | mm/s | float |

### Nhóm 4: Lube Oil (3 signals)

| OPC UA NodeId | Category | Unit | Type |
|---|---|---|---|
| `ns=2;s=COMP01_LO_PRESS` | industrial_signal | kPa | float |
| `ns=2;s=COMP01_LO_TEMP` | industrial_signal | °C | float |
| `ns=2;s=COMP01_LO_FILTER_DP` | industrial_signal | kPa | float |

### Nhóm 5: Cooling System (2 signals)

| OPC UA NodeId | Category | Unit | Type |
|---|---|---|---|
| `ns=2;s=COMP01_CW_SUPPLY_TEMP` | industrial_signal | °C | float |
| `ns=2;s=COMP01_CW_RETURN_TEMP` | industrial_signal | °C | float |

### Nhóm 6: Seal Gas + Speed + Power (3 signals)

| OPC UA NodeId | Category | Unit | Type |
|---|---|---|---|
| `ns=2;s=COMP01_SEAL_FLOW` | industrial_signal | Nm³/h | float |
| `ns=2;s=COMP01_SPEED` | industrial_signal | RPM | float |
| `ns=2;s=COMP01_POWER` | industrial_signal | kW | float |

### Nhóm 7: Alarms (7 signals)

| OPC UA NodeId | Category | Type |
|---|---|---|
| `ns=2;s=ALM_COMP01_VIB_HIGH` | industrial_event | bool |
| `ns=2;s=ALM_COMP01_VIB_NDE_HIGH` | industrial_event | bool |
| `ns=2;s=ALM_COMP01_BRG_TEMP_HIGH` | industrial_event | bool |
| `ns=2;s=ALM_COMP01_LO_PRESS_LOW` | industrial_event | bool |
| `ns=2;s=ALM_COMP01_DISCH_TEMP_HIGH` | industrial_event | bool |
| `ns=2;s=ALM_COMP01_MOTOR_CURRENT_HIGH` | industrial_event | bool |
| `ns=2;s=ALM_COMP01_SEAL_FLOW_HIGH` | industrial_event | bool |

> **Tổng: 25 measurement signals + 7 alarm signals = 32 OPC UA variables**

---

## PlantOS CDM Mapping

### Asset Tree

```
VF-DEMO (plant)
└── COMPRESSOR-AREA (area)
    └── COMP01 (Compressor Train A, asset_type: compressor_train)
        ├── COMP01-MOTOR (Drive Motor, asset_type: motor)
        ├── COMP01-CORE (Compressor Core, asset_type: compressor)
        ├── COMP01-BEARINGS (Bearings, asset_type: bearing_assembly)
        ├── COMP01-LUBE (Lube Oil System, asset_type: lubrication_system)
        ├── COMP01-COOLING (Cooling System, asset_type: cooling_system)
        └── COMP01-SEAL (Seal Gas System, asset_type: seal_system)
```

### Full Signal Mapping Table

| # | OPC UA NodeId | PlantOS Asset | PlantOS Signal ID | Unit | Scale |
|---|---|---|---|---|---|
| **Compressor Core** |
| 1 | `COMP01_SUCTION_PRESSURE` | COMP01-CORE | `COMP01-CORE.suction_pressure` | kPa | 1.0 |
| 2 | `COMP01_DISCHARGE_PRESSURE` | COMP01-CORE | `COMP01-CORE.discharge_pressure` | kPa | 1.0 |
| 3 | `COMP01_FLOW` | COMP01-CORE | `COMP01-CORE.flow_rate` | m³/h | ×3600 |
| 4 | `COMP01_SUCTION_TEMP` | COMP01-CORE | `COMP01-CORE.suction_temp` | °C | 1.0 |
| 5 | `COMP01_DISCHARGE_TEMP` | COMP01-CORE | `COMP01-CORE.discharge_temp` | °C | 1.0 |
| **Motor** |
| 6 | `COMP01_MOTOR_CURRENT` | COMP01-MOTOR | `COMP01-MOTOR.current` | A | 1.0 |
| 7 | `COMP01_MOTOR_POWER` | COMP01-MOTOR | `COMP01-MOTOR.power` | kW | 1.0 |
| 8 | `COMP01_MOTOR_WINDING_TEMP` | COMP01-MOTOR | `COMP01-MOTOR.winding_temp` | °C | 1.0 |
| 9 | `COMP01_MOTOR_BRG_DE_TEMP` | COMP01-MOTOR | `COMP01-MOTOR.bearing_de_temp` | °C | 1.0 |
| 10 | `COMP01_MOTOR_BRG_NDE_TEMP` | COMP01-MOTOR | `COMP01-MOTOR.bearing_nde_temp` | °C | 1.0 |
| 11 | `COMP01_MOTOR_VIB_DE` | COMP01-MOTOR | `COMP01-MOTOR.vibration_de` | mm/s | 1.0 |
| 12 | `COMP01_MOTOR_VIB_NDE` | COMP01-MOTOR | `COMP01-MOTOR.vibration_nde` | mm/s | 1.0 |
| **Bearings** |
| 13 | `COMP01_BRG_DE_TEMP` | COMP01-BEARINGS | `COMP01-BEARINGS.de_temp` | °C | 1.0 |
| 14 | `COMP01_BRG_NDE_TEMP` | COMP01-BEARINGS | `COMP01-BEARINGS.nde_temp` | °C | 1.0 |
| 15 | `COMP01_BRG_THRUST_TEMP` | COMP01-BEARINGS | `COMP01-BEARINGS.thrust_temp` | °C | 1.0 |
| 16 | `COMP01_VIB_DE` | COMP01-BEARINGS | `COMP01-BEARINGS.vibration_de` | mm/s | 1.0 |
| 17 | `COMP01_VIB_NDE` | COMP01-BEARINGS | `COMP01-BEARINGS.vibration_nde` | mm/s | 1.0 |
| 18 | `COMP01_VIB_AXIAL` | COMP01-BEARINGS | `COMP01-BEARINGS.vibration_axial` | mm/s | 1.0 |
| **Lube Oil** |
| 19 | `COMP01_LO_PRESS` | COMP01-LUBE | `COMP01-LUBE.pressure` | kPa | 1.0 |
| 20 | `COMP01_LO_TEMP` | COMP01-LUBE | `COMP01-LUBE.temperature` | °C | 1.0 |
| 21 | `COMP01_LO_FILTER_DP` | COMP01-LUBE | `COMP01-LUBE.filter_dp` | kPa | 1.0 |
| **Cooling** |
| 22 | `COMP01_CW_SUPPLY_TEMP` | COMP01-COOLING | `COMP01-COOLING.supply_temp` | °C | 1.0 |
| 23 | `COMP01_CW_RETURN_TEMP` | COMP01-COOLING | `COMP01-COOLING.return_temp` | °C | 1.0 |
| **Seal Gas + Speed + Power** |
| 24 | `COMP01_SEAL_FLOW` | COMP01-SEAL | `COMP01-SEAL.flow_rate` | Nm³/h | 1.0 |
| 25 | `COMP01_SPEED` | COMP01-CORE | `COMP01-CORE.speed` | RPM | 1.0 |
| 26 | `COMP01_POWER` | COMP01-CORE | `COMP01-CORE.power` | kW | 1.0 |

---

## Implementation Checklist

- [ ] CREATE `edge/agent/collectors/opcua/__init__.py`
- [ ] CREATE `edge/agent/collectors/opcua/client.py` — OPC UA async client wrapper
- [ ] CREATE `edge/agent/collectors/opcua/mapper.py` — NodeId → signal_id mapping
- [ ] CREATE `edge/agent/collectors/opcua/collector.py` — poll loop, normalization
- [ ] MODIFY `edge/agent/main.py` — integrate OPC UA collector
- [ ] MODIFY `edge/agent/config.yaml` — add `opcua:` section with 26 tags
- [ ] MODIFY `edge/agent/web.py` — add OPC UA status to /api/status
- [ ] MODIFY `edge/agent/requirements.txt` — add `asyncua>=1.1.0`
- [ ] CREATE `backend/app/seed/vf_demo_plant.py` — seed data (7 assets + 26 signals)
- [ ] CREATE `docs/adr/ADR-0004-opcua-cdm-mapping.md` — ADR document

---

## Detailed Instructions

### 1. `edge/agent/collectors/opcua/client.py`

```python
"""OPC UA async client for reading industrial signals from Virtual Factory."""

import asyncio
import logging
from typing import Any

logger = logging.getLogger(__name__)


class OpcUaClient:
    """Async OPC UA client that connects to a server and reads variable values."""

    def __init__(self, endpoint: str, timeout: float = 5.0):
        self.endpoint = endpoint
        self.timeout = timeout
        self._client: Any = None
        self._connected = False

    @property
    def is_connected(self) -> bool:
        return self._connected and self._client is not None

    async def connect(self, retries: int = 10, delay_s: float = 2.0) -> bool:
        """Connect to OPC UA server with retry logic."""
        try:
            from asyncua import Client
        except ImportError:
            logger.error("asyncua not installed. Run: pip install asyncua")
            return False

        for attempt in range(1, retries + 1):
            try:
                self._client = Client(url=self.endpoint, timeout=self.timeout)
                await self._client.connect()
                self._connected = True
                logger.info(f"Connected to OPC UA server at {self.endpoint}")
                return True
            except Exception as e:
                logger.warning(f"OPC UA connect attempt {attempt}/{retries}: {e}")
                if self._client:
                    try:
                        await self._client.disconnect()
                    except Exception:
                        pass
                    self._client = None
                if attempt < retries:
                    await asyncio.sleep(delay_s)

        logger.error(f"Failed to connect to OPC UA server after {retries} attempts")
        return False

    async def disconnect(self) -> None:
        if self._client:
            try:
                await self._client.disconnect()
            except Exception:
                pass
            self._client = None
        self._connected = False

    async def read_value(self, node_id: str) -> Any | None:
        if not self.is_connected:
            return None
        try:
            node = self._client.get_node(node_id)
            return await node.read_value()
        except Exception as e:
            logger.error(f"Failed to read {node_id}: {e}")
            return None

    async def read_values(self, node_ids: list[str]) -> dict[str, Any]:
        if not self.is_connected:
            return {}
        results = {}
        for nid in node_ids:
            value = await self.read_value(nid)
            if value is not None:
                results[nid] = value
        return results
```

### 2. `edge/agent/collectors/opcua/mapper.py`

```python
"""NodeId → PlantOS signal_id mapping with unit conversion."""

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class SignalMapping:
    node_id: str
    signal_id: str
    scale: float = 1.0
    offset: float = 0.0


class OpcUaMapper:
    """Maps OPC UA NodeIds to PlantOS signal_ids with optional conversion."""

    def __init__(self, tags: list[dict]):
        self.mappings: list[SignalMapping] = []
        for tag in tags:
            self.mappings.append(SignalMapping(
                node_id=tag["node_id"],
                signal_id=tag["signal_id"],
                scale=tag.get("scale", 1.0),
                offset=tag.get("offset", 0.0),
            ))

    @property
    def node_ids(self) -> list[str]:
        return [m.node_id for m in self.mappings]

    def map_values(self, raw: dict[str, float | bool | int | None]) -> list[dict]:
        results = []
        for mapping in self.mappings:
            value = raw.get(mapping.node_id)
            if value is None:
                continue
            try:
                converted = float(value) * mapping.scale + mapping.offset
            except (TypeError, ValueError):
                converted = value
            results.append({
                "signal_id": mapping.signal_id,
                "value": round(converted, 4) if isinstance(converted, float) else converted,
            })
        return results
```

### 3. `edge/agent/collectors/opcua/collector.py`

```python
"""OPC UA collector — poll NodeIds, normalize, write to DuckDB."""

import asyncio
import logging
from datetime import datetime, timezone

from .client import OpcUaClient
from .mapper import OpcUaMapper

logger = logging.getLogger(__name__)


class OpcUaCollector:
    """Polls OPC UA server periodically, maps values, writes to local buffer."""

    def __init__(self, config: dict, buffer):
        self.config = config
        self.buffer = buffer
        self.client = OpcUaClient(
            endpoint=config.get("endpoint", "opc.tcp://127.0.0.1:4840"),
            timeout=config.get("timeout", 5.0),
        )
        self.mapper = OpcUaMapper(config.get("tags", []))
        self.interval = config.get("poll_interval_ms", 1000) / 1000
        self._enabled = config.get("enabled", False)
        self._task: asyncio.Task | None = None

    @property
    def connected(self) -> bool:
        return self.client.is_connected

    async def start(self):
        if not self._enabled:
            logger.info("OPC UA collector disabled")
            return

        connected = await self.client.connect()
        if not connected:
            logger.warning("OPC UA collector: initial connection failed, retrying...")
            self._task = asyncio.create_task(self._retry_connect())
            return

        logger.info(f"OPC UA collector started ({len(self.mapper.node_ids)} signals)")
        self._task = asyncio.create_task(self._poll_loop())

    async def _retry_connect(self):
        while not self.client.is_connected:
            await asyncio.sleep(10)
            await self.client.connect()

    async def _poll_loop(self):
        while self.client.is_connected:
            try:
                raw = await self.client.read_values(self.mapper.node_ids)
                if raw:
                    measurements = self.mapper.map_values(raw)
                    if measurements:
                        now = datetime.now(timezone.utc)
                        rows = [
                            {
                                "timestamp": now.isoformat(),
                                "signal_id": m["signal_id"],
                                "value": m["value"],
                                "quality": "GOOD",
                                "source": "opcua",
                            }
                            for m in measurements
                        ]
                        self.buffer.write(rows)
            except Exception as e:
                logger.error(f"OPC UA poll error: {e}")
            await asyncio.sleep(self.interval)

    async def stop(self):
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        await self.client.disconnect()
```

### 4. `edge/agent/collectors/opcua/__init__.py`

```python
"""OPC UA protocol collector for Virtual Factory integration."""
from .collector import OpcUaCollector
```

### 5. Modify `edge/agent/main.py`

**A. Sau dòng `self.generators = [...]` thêm:**

```python
        # OPC UA collector (for Virtual Factory integration)
        from collectors.opcua import OpcUaCollector
        opcua_cfg = self.cfg.get("opcua", {})
        self.opcua_collector = OpcUaCollector(opcua_cfg, self.buffer)
```

**B. Trong `async def start(self)`, trước `self.mqtt.connect()` thêm:**

```python
        if hasattr(self, 'opcua_collector'):
            await self.opcua_collector.start()
```

**C. Trong `async def stop(self)` thêm:**

```python
        if hasattr(self, 'opcua_collector'):
            await self.opcua_collector.stop()
```

**D. Thêm method:**

```python
    def get_opcua_status(self) -> dict:
        if not hasattr(self, 'opcua_collector'):
            return {"enabled": False}
        return {
            "enabled": self.opcua_collector._enabled,
            "connected": self.opcua_collector.connected,
            "endpoint": self.opcua_collector.config.get("endpoint", ""),
            "signal_count": len(self.opcua_collector.mapper.node_ids),
        }
```

### 6. Modify `edge/agent/config.yaml`

Thêm section OPC UA:

```yaml
# OPC UA collector (Virtual Factory Compressor Train)
opcua:
  enabled: false           # set to true to enable
  endpoint: opc.tcp://host.docker.internal:4840
  timeout: 5.0
  poll_interval_ms: 1000
  tags:
    # === Compressor Core (5) ===
    - node_id: ns=2;s=COMP01_SUCTION_PRESSURE
      signal_id: COMP01-CORE.suction_pressure
    - node_id: ns=2;s=COMP01_DISCHARGE_PRESSURE
      signal_id: COMP01-CORE.discharge_pressure
    - node_id: ns=2;s=COMP01_FLOW
      signal_id: COMP01-CORE.flow_rate
      scale: 3600.0     # m³/s → m³/h
    - node_id: ns=2;s=COMP01_SUCTION_TEMP
      signal_id: COMP01-CORE.suction_temp
    - node_id: ns=2;s=COMP01_DISCHARGE_TEMP
      signal_id: COMP01-CORE.discharge_temp
    # === Motor (7) ===
    - node_id: ns=2;s=COMP01_MOTOR_CURRENT
      signal_id: COMP01-MOTOR.current
    - node_id: ns=2;s=COMP01_MOTOR_POWER
      signal_id: COMP01-MOTOR.power
    - node_id: ns=2;s=COMP01_MOTOR_WINDING_TEMP
      signal_id: COMP01-MOTOR.winding_temp
    - node_id: ns=2;s=COMP01_MOTOR_BRG_DE_TEMP
      signal_id: COMP01-MOTOR.bearing_de_temp
    - node_id: ns=2;s=COMP01_MOTOR_BRG_NDE_TEMP
      signal_id: COMP01-MOTOR.bearing_nde_temp
    - node_id: ns=2;s=COMP01_MOTOR_VIB_DE
      signal_id: COMP01-MOTOR.vibration_de
    - node_id: ns=2;s=COMP01_MOTOR_VIB_NDE
      signal_id: COMP01-MOTOR.vibration_nde
    # === Bearings (6) ===
    - node_id: ns=2;s=COMP01_BRG_DE_TEMP
      signal_id: COMP01-BEARINGS.de_temp
    - node_id: ns=2;s=COMP01_BRG_NDE_TEMP
      signal_id: COMP01-BEARINGS.nde_temp
    - node_id: ns=2;s=COMP01_BRG_THRUST_TEMP
      signal_id: COMP01-BEARINGS.thrust_temp
    - node_id: ns=2;s=COMP01_VIB_DE
      signal_id: COMP01-BEARINGS.vibration_de
    - node_id: ns=2;s=COMP01_VIB_NDE
      signal_id: COMP01-BEARINGS.vibration_nde
    - node_id: ns=2;s=COMP01_VIB_AXIAL
      signal_id: COMP01-BEARINGS.vibration_axial
    # === Lube Oil (3) ===
    - node_id: ns=2;s=COMP01_LO_PRESS
      signal_id: COMP01-LUBE.pressure
    - node_id: ns=2;s=COMP01_LO_TEMP
      signal_id: COMP01-LUBE.temperature
    - node_id: ns=2;s=COMP01_LO_FILTER_DP
      signal_id: COMP01-LUBE.filter_dp
    # === Cooling (2) ===
    - node_id: ns=2;s=COMP01_CW_SUPPLY_TEMP
      signal_id: COMP01-COOLING.supply_temp
    - node_id: ns=2;s=COMP01_CW_RETURN_TEMP
      signal_id: COMP01-COOLING.return_temp
    # === Seal Gas + Speed + Power (3) ===
    - node_id: ns=2;s=COMP01_SEAL_FLOW
      signal_id: COMP01-SEAL.flow_rate
    - node_id: ns=2;s=COMP01_SPEED
      signal_id: COMP01-CORE.speed
    - node_id: ns=2;s=COMP01_POWER
      signal_id: COMP01-CORE.power
```

### 7. `edge/agent/requirements.txt`

```
asyncua>=1.1.0
```

### 8. `edge/agent/web.py`

Trong handler `/api/status`, thêm key:

```python
        "opcua": agent.get_opcua_status() if hasattr(agent, 'get_opcua_status') else {"enabled": False},
```

### 9. `backend/app/seed/vf_demo_plant.py`

```python
"""Seed data for Virtual Factory Compressor Train plant assets and signals."""

VF_PLANT = {
    "plant_id": "VF-DEMO",
    "plant_code": "VF-DEMO",
    "name": "Virtual Factory Demo Plant",
    "description": "Compressor Train Analytics Benchmark",
}

VF_AREA = {
    "area_id": "COMPRESSOR-AREA",
    "area_code": "COMPRESSOR-AREA",
    "name": "Compressor Area",
    "plant_id": "VF-DEMO",
}

VF_ASSETS = [
    {"asset_id": "COMP01", "asset_code": "COMP01", "name": "Compressor Train A",
     "asset_type": "compressor_train", "parent_asset_id": None,
     "plant_id": "VF-DEMO", "area_id": "COMPRESSOR-AREA", "criticality": "critical"},
    {"asset_id": "COMP01-MOTOR", "asset_code": "COMP01-MOTOR", "name": "Drive Motor",
     "asset_type": "motor", "parent_asset_id": "COMP01",
     "plant_id": "VF-DEMO", "area_id": "COMPRESSOR-AREA", "criticality": "critical"},
    {"asset_id": "COMP01-CORE", "asset_code": "COMP01-CORE", "name": "Compressor Core",
     "asset_type": "compressor", "parent_asset_id": "COMP01",
     "plant_id": "VF-DEMO", "area_id": "COMPRESSOR-AREA", "criticality": "critical"},
    {"asset_id": "COMP01-BEARINGS", "asset_code": "COMP01-BEARINGS", "name": "Bearings Assembly",
     "asset_type": "bearing_assembly", "parent_asset_id": "COMP01",
     "plant_id": "VF-DEMO", "area_id": "COMPRESSOR-AREA", "criticality": "high"},
    {"asset_id": "COMP01-LUBE", "asset_code": "COMP01-LUBE", "name": "Lube Oil System",
     "asset_type": "lubrication_system", "parent_asset_id": "COMP01",
     "plant_id": "VF-DEMO", "area_id": "COMPRESSOR-AREA", "criticality": "high"},
    {"asset_id": "COMP01-COOLING", "asset_code": "COMP01-COOLING", "name": "Cooling Water System",
     "asset_type": "cooling_system", "parent_asset_id": "COMP01",
     "plant_id": "VF-DEMO", "area_id": "COMPRESSOR-AREA", "criticality": "medium"},
    {"asset_id": "COMP01-SEAL", "asset_code": "COMP01-SEAL", "name": "Seal Gas System",
     "asset_type": "seal_system", "parent_asset_id": "COMP01",
     "plant_id": "VF-DEMO", "area_id": "COMPRESSOR-AREA", "criticality": "high"},
]

VF_SIGNALS = [
    # Compressor Core (7)
    {"signal_id": "COMP01-CORE.suction_pressure", "asset_id": "COMP01-CORE",
     "signal_name": "suction_pressure", "display_name": "Suction Pressure",
     "signal_type": "measurement", "data_type": "float", "engineering_unit": "kPa",
     "source": {"source_type": "opcua", "source_ref": "ns=2;s=COMP01_SUCTION_PRESSURE"}},
    {"signal_id": "COMP01-CORE.discharge_pressure", "asset_id": "COMP01-CORE",
     "signal_name": "discharge_pressure", "display_name": "Discharge Pressure",
     "signal_type": "measurement", "data_type": "float", "engineering_unit": "kPa",
     "source": {"source_type": "opcua", "source_ref": "ns=2;s=COMP01_DISCHARGE_PRESSURE"}},
    {"signal_id": "COMP01-CORE.flow_rate", "asset_id": "COMP01-CORE",
     "signal_name": "flow_rate", "display_name": "Flow Rate",
     "signal_type": "measurement", "data_type": "float", "engineering_unit": "m3/h",
     "source": {"source_type": "opcua", "source_ref": "ns=2;s=COMP01_FLOW"}},
    {"signal_id": "COMP01-CORE.suction_temp", "asset_id": "COMP01-CORE",
     "signal_name": "suction_temp", "display_name": "Suction Temperature",
     "signal_type": "measurement", "data_type": "float", "engineering_unit": "degC",
     "source": {"source_type": "opcua", "source_ref": "ns=2;s=COMP01_SUCTION_TEMP"}},
    {"signal_id": "COMP01-CORE.discharge_temp", "asset_id": "COMP01-CORE",
     "signal_name": "discharge_temp", "display_name": "Discharge Temperature",
     "signal_type": "measurement", "data_type": "float", "engineering_unit": "degC",
     "source": {"source_type": "opcua", "source_ref": "ns=2;s=COMP01_DISCHARGE_TEMP"}},
    {"signal_id": "COMP01-CORE.speed", "asset_id": "COMP01-CORE",
     "signal_name": "speed", "display_name": "Rotational Speed",
     "signal_type": "measurement", "data_type": "float", "engineering_unit": "RPM",
     "source": {"source_type": "opcua", "source_ref": "ns=2;s=COMP01_SPEED"}},
    {"signal_id": "COMP01-CORE.power", "asset_id": "COMP01-CORE",
     "signal_name": "power", "display_name": "Power Consumption",
     "signal_type": "measurement", "data_type": "float", "engineering_unit": "kW",
     "source": {"source_type": "opcua", "source_ref": "ns=2;s=COMP01_POWER"}},
    # Motor (7)
    {"signal_id": "COMP01-MOTOR.current", "asset_id": "COMP01-MOTOR",
     "signal_name": "current", "display_name": "Motor Current",
     "signal_type": "measurement", "data_type": "float", "engineering_unit": "A",
     "source": {"source_type": "opcua", "source_ref": "ns=2;s=COMP01_MOTOR_CURRENT"}},
    {"signal_id": "COMP01-MOTOR.power", "asset_id": "COMP01-MOTOR",
     "signal_name": "power", "display_name": "Motor Power",
     "signal_type": "measurement", "data_type": "float", "engineering_unit": "kW",
     "source": {"source_type": "opcua", "source_ref": "ns=2;s=COMP01_MOTOR_POWER"}},
    {"signal_id": "COMP01-MOTOR.winding_temp", "asset_id": "COMP01-MOTOR",
     "signal_name": "winding_temp", "display_name": "Winding Temperature",
     "signal_type": "measurement", "data_type": "float", "engineering_unit": "degC",
     "source": {"source_type": "opcua", "source_ref": "ns=2;s=COMP01_MOTOR_WINDING_TEMP"}},
    {"signal_id": "COMP01-MOTOR.bearing_de_temp", "asset_id": "COMP01-MOTOR",
     "signal_name": "bearing_de_temp", "display_name": "Motor DE Bearing Temp",
     "signal_type": "measurement", "data_type": "float", "engineering_unit": "degC",
     "source": {"source_type": "opcua", "source_ref": "ns=2;s=COMP01_MOTOR_BRG_DE_TEMP"}},
    {"signal_id": "COMP01-MOTOR.bearing_nde_temp", "asset_id": "COMP01-MOTOR",
     "signal_name": "bearing_nde_temp", "display_name": "Motor NDE Bearing Temp",
     "signal_type": "measurement", "data_type": "float", "engineering_unit": "degC",
     "source": {"source_type": "opcua", "source_ref": "ns=2;s=COMP01_MOTOR_BRG_NDE_TEMP"}},
    {"signal_id": "COMP01-MOTOR.vibration_de", "asset_id": "COMP01-MOTOR",
     "signal_name": "vibration_de", "display_name": "Motor DE Vibration",
     "signal_type": "measurement", "data_type": "float", "engineering_unit": "mm/s",
     "source": {"source_type": "opcua", "source_ref": "ns=2;s=COMP01_MOTOR_VIB_DE"}},
    {"signal_id": "COMP01-MOTOR.vibration_nde", "asset_id": "COMP01-MOTOR",
     "signal_name": "vibration_nde", "display_name": "Motor NDE Vibration",
     "signal_type": "measurement", "data_type": "float", "engineering_unit": "mm/s",
     "source": {"source_type": "opcua", "source_ref": "ns=2;s=COMP01_MOTOR_VIB_NDE"}},
    # Bearings (6)
    {"signal_id": "COMP01-BEARINGS.de_temp", "asset_id": "COMP01-BEARINGS",
     "signal_name": "de_temp", "display_name": "DE Bearing Temperature",
     "signal_type": "measurement", "data_type": "float", "engineering_unit": "degC",
     "source": {"source_type": "opcua", "source_ref": "ns=2;s=COMP01_BRG_DE_TEMP"}},
    {"signal_id": "COMP01-BEARINGS.nde_temp", "asset_id": "COMP01-BEARINGS",
     "signal_name": "nde_temp", "display_name": "NDE Bearing Temperature",
     "signal_type": "measurement", "data_type": "float", "engineering_unit": "degC",
     "source": {"source_type": "opcua", "source_ref": "ns=2;s=COMP01_BRG_NDE_TEMP"}},
    {"signal_id": "COMP01-BEARINGS.thrust_temp", "asset_id": "COMP01-BEARINGS",
     "signal_name": "thrust_temp", "display_name": "Thrust Bearing Temperature",
     "signal_type": "measurement", "data_type": "float", "engineering_unit": "degC",
     "source": {"source_type": "opcua", "source_ref": "ns=2;s=COMP01_BRG_THRUST_TEMP"}},
    {"signal_id": "COMP01-BEARINGS.vibration_de", "asset_id": "COMP01-BEARINGS",
     "signal_name": "vibration_de", "display_name": "DE Vibration",
     "signal_type": "measurement", "data_type": "float", "engineering_unit": "mm/s",
     "source": {"source_type": "opcua", "source_ref": "ns=2;s=COMP01_VIB_DE"}},
    {"signal_id": "COMP01-BEARINGS.vibration_nde", "asset_id": "COMP01-BEARINGS",
     "signal_name": "vibration_nde", "display_name": "NDE Vibration",
     "signal_type": "measurement", "data_type": "float", "engineering_unit": "mm/s",
     "source": {"source_type": "opcua", "source_ref": "ns=2;s=COMP01_VIB_NDE"}},
    {"signal_id": "COMP01-BEARINGS.vibration_axial", "asset_id": "COMP01-BEARINGS",
     "signal_name": "vibration_axial", "display_name": "Axial Vibration",
     "signal_type": "measurement", "data_type": "float", "engineering_unit": "mm/s",
     "source": {"source_type": "opcua", "source_ref": "ns=2;s=COMP01_VIB_AXIAL"}},
    # Lube Oil (3)
    {"signal_id": "COMP01-LUBE.pressure", "asset_id": "COMP01-LUBE",
     "signal_name": "pressure", "display_name": "Lube Oil Pressure",
     "signal_type": "measurement", "data_type": "float", "engineering_unit": "kPa",
     "source": {"source_type": "opcua", "source_ref": "ns=2;s=COMP01_LO_PRESS"}},
    {"signal_id": "COMP01-LUBE.temperature", "asset_id": "COMP01-LUBE",
     "signal_name": "temperature", "display_name": "Lube Oil Temperature",
     "signal_type": "measurement", "data_type": "float", "engineering_unit": "degC",
     "source": {"source_type": "opcua", "source_ref": "ns=2;s=COMP01_LO_TEMP"}},
    {"signal_id": "COMP01-LUBE.filter_dp", "asset_id": "COMP01-LUBE",
     "signal_name": "filter_dp", "display_name": "Filter Differential Pressure",
     "signal_type": "measurement", "data_type": "float", "engineering_unit": "kPa",
     "source": {"source_type": "opcua", "source_ref": "ns=2;s=COMP01_LO_FILTER_DP"}},
    # Cooling (2)
    {"signal_id": "COMP01-COOLING.supply_temp", "asset_id": "COMP01-COOLING",
     "signal_name": "supply_temp", "display_name": "Cooling Water Supply Temp",
     "signal_type": "measurement", "data_type": "float", "engineering_unit": "degC",
     "source": {"source_type": "opcua", "source_ref": "ns=2;s=COMP01_CW_SUPPLY_TEMP"}},
    {"signal_id": "COMP01-COOLING.return_temp", "asset_id": "COMP01-COOLING",
     "signal_name": "return_temp", "display_name": "Cooling Water Return Temp",
     "signal_type": "measurement", "data_type": "float", "engineering_unit": "degC",
     "source": {"source_type": "opcua", "source_ref": "ns=2;s=COMP01_CW_RETURN_TEMP"}},
    # Seal Gas (1)
    {"signal_id": "COMP01-SEAL.flow_rate", "asset_id": "COMP01-SEAL",
     "signal_name": "flow_rate", "display_name": "Seal Gas Flow",
     "signal_type": "measurement", "data_type": "float", "engineering_unit": "Nm3/h",
     "source": {"source_type": "opcua", "source_ref": "ns=2;s=COMP01_SEAL_FLOW"}},
]


async def seed_vf_demo_plant(asset_service, signal_service):
    """Seed Virtual Factory Compressor Train demo plant."""
    try:
        await asset_service.create_plant(VF_PLANT)
    except Exception:
        pass
    try:
        await asset_service.create_area(VF_AREA)
    except Exception:
        pass
    for asset_data in VF_ASSETS:
        try:
            await asset_service.create(asset_data)
        except Exception:
            pass
    for signal_data in VF_SIGNALS:
        try:
            await signal_service.create(signal_data)
        except Exception:
            pass
```

### 10. ADR: `docs/adr/ADR-0004-opcua-cdm-mapping.md`

```markdown
# ADR-0004: OPC UA → PlantOS CDM Mapping

## Status
Accepted

## Context
PlantOS integrates with Virtual Factory via OPC UA. VF publishes raw OPC UA variables
with flat NodeIds. PlantOS must map these to hierarchical CDM signal_ids.

## Decision

### 1. Collector Pattern
Same as Modbus collector: client → mapper → collector → DuckDB → sync.

### 2. Asset Hierarchy
PlantOS assets mirror sub-system structure:
- COMP01 (compressor_train) → COMP01-MOTOR, COMP01-CORE, COMP01-BEARINGS,
  COMP01-LUBE, COMP01-COOLING, COMP01-SEAL

### 3. Signal Naming
`{ASSET_ID}.{physical_property}` — e.g. `COMP01-MOTOR.vibration_de`

### 4. Unit Conversion
Edge mapper handles: `COMP01_FLOW` m³/s × 3600 → m³/h. All others 1:1.

### 5. Virtual Factory Independence
VF knows nothing about PlantOS CDM. All CDM packaging in PlantOS Edge + Center.

## Consequences
- VF deployable independently
- Pattern reusable for any OPC UA source
- Asset hierarchy enables sub-system analytics drill-down
```

---

## Validation

```bash
# 1. Start Virtual Factory Compressor Train
cd D:\Project\Github\virtual-factory
docker compose up --build -d
# OPC UA server at opc.tcp://localhost:4840

# 2. Start PlantOS
cd D:\Project\Github\PlantOS\deployment
docker compose up -d postgres tdengine emqx backend frontend

# 3. Seed VF plant
curl -X POST http://localhost:8000/api/v1/seed/vf-demo

# 4. Start Edge Agent (enable opcua.enabled: true)
cd D:\Project\Github\PlantOS\edge\agent
pip install asyncua
python main.py

# 5. Verify
curl http://localhost:8001/api/status
# → opcua.enabled=true, opcua.connected=true, signal_count=26

curl "http://localhost:8000/api/v1/measurements/current?asset_id=COMP01-MOTOR"
# → 7 signals: current, power, winding_temp, bearing_de_temp, bearing_nde_temp,
#   vibration_de, vibration_nde

curl "http://localhost:8000/api/v1/measurements/current?asset_id=COMP01-CORE"
# → 7 signals: suction_pressure, discharge_pressure, flow_rate, suction_temp,
#   discharge_temp, speed, power

# 6. UI
open http://localhost:5173/historian
# Add COMP01-CORE.flow_rate — expect daily_shift pattern
# Add COMP01-MOTOR.vibration_de — expect baseline ~2-3 mm/s
```

---

## Files Summary

| # | File | Action | Description |
|---|------|--------|-------------|
| 1 | `edge/agent/collectors/opcua/__init__.py` | CREATE | Package init |
| 2 | `edge/agent/collectors/opcua/client.py` | CREATE | OPC UA async client |
| 3 | `edge/agent/collectors/opcua/mapper.py` | CREATE | NodeId → signal_id mapper |
| 4 | `edge/agent/collectors/opcua/collector.py` | CREATE | Poll loop (26 signals) |
| 5 | `edge/agent/main.py` | MODIFY | Integrate OPC UA collector |
| 6 | `edge/agent/config.yaml` | MODIFY | Add opcua section (26 tags) |
| 7 | `edge/agent/requirements.txt` | MODIFY | Add asyncua |
| 8 | `edge/agent/web.py` | MODIFY | Add OPC UA status to /api/status |
| 9 | `backend/app/seed/vf_demo_plant.py` | CREATE | Seed data (7 assets, 26 signals) |
| 10 | `docs/adr/ADR-0004-opcua-cdm-mapping.md` | CREATE | ADR document |

## Handoff to Coder

```
Đọc prompt: docs/prompts/phase5-task02-opcua-integration.md
10 files (5 CREATE, 5 MODIFY).
Compressor Train Benchmark — 26 OPC UA signals, 7 assets, 6 sub-systems.
Pattern: client → mapper → collector (giống Modbus collector).
Virtual Factory KHÔNG sửa — chỉ docker compose up.
Seed data: VF-DEMO plant, COMP01 + 6 sub-assets, 26 signals.
Validate: curl /api/v1/measurements/current?asset_id=COMP01-MOTOR → 7 signals.
```
