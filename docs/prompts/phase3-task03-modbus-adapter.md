# Phase 3 — Task 3-03: Modbus TCP Adapter + Protocol Setup UI

> **Designer:** DeepSeek V4 Pro | **Date:** 2026-06-30
> **Phase 3 wrap-up!**

## Context

Thêm Modbus TCP protocol adapter vào Edge Agent. Edge dashboard có UI setup form để cấu hình connection + tag mapping. Đây là protocol adapter đầu tiên — thiết lập pattern cho OPC UA sau này.

## Architecture

```
Edge Agent
├── collectors/modbus/
│   ├── __init__.py
│   ├── client.py       ← Modbus TCP client (pymodbus)
│   ├── mapper.py       ← Tag mapping: register → signal_id
│   └── collector.py    ← Poll loop: read → normalize → DuckDB
├── web.py              ← MODIFY: protocol status + setup form
├── config.yaml         ← MODIFY: modbus section
└── templates/
    └── setup.html       ← Protocol setup page
```

## Implementation Checklist

- [ ] CREATE `edge/agent/collectors/__init__.py`
- [ ] CREATE `edge/agent/collectors/modbus/__init__.py`
- [ ] CREATE `edge/agent/collectors/modbus/client.py` — Modbus TCP connection
- [ ] CREATE `edge/agent/collectors/modbus/mapper.py` — Tag mapping logic
- [ ] CREATE `edge/agent/collectors/modbus/collector.py` — Poll + normalize
- [ ] MODIFY `edge/agent/web.py` — protocol status + setup API + form page
- [ ] CREATE `edge/agent/templates/setup.html` — Protocol setup UI
- [ ] MODIFY `edge/agent/config.yaml` — add modbus section
- [ ] MODIFY `edge/agent/requirements.txt` — +pymodbus
- [ ] MODIFY `edge/agent/main.py` — integrate modbus collector

## Detailed Instructions

### 1. `edge/agent/requirements.txt` — Add

```
pymodbus>=3.7.0
```

### 2. `edge/agent/config.yaml` — Add Modbus Section

```yaml
modbus:
  enabled: true
  host: 127.0.0.1
  port: 502
  unit_id: 1
  poll_interval_ms: 1000
  tags:
    - register: 40001
      type: holding
      data_type: float
      signal_id: PUMP-101.discharge_pressure
      scale: 1.0
      offset: 0.0
    - register: 40002
      type: holding
      data_type: float
      signal_id: PUMP-101.flow_rate
      scale: 0.1
      offset: 0.0
    - register: 00001
      type: coil
      data_type: bool
      signal_id: PUMP-101.running_status
```

### 3. `edge/agent/collectors/modbus/client.py`

```python
"""Modbus TCP client wrapper."""

import logging
from pymodbus.client import ModbusTcpClient

logger = logging.getLogger(__name__)


class ModbusClient:
    def __init__(self, host: str = "127.0.0.1", port: int = 502, unit_id: int = 1):
        self.host = host
        self.port = port
        self.unit_id = unit_id
        self.client = ModbusTcpClient(host, port)
        self._connected = False

    def connect(self) -> bool:
        try:
            self._connected = self.client.connect()
            if self._connected:
                logger.info(f"Modbus connected: {self.host}:{self.port}")
            return self._connected
        except Exception as e:
            logger.warning(f"Modbus connect failed: {e}")
            return False

    def disconnect(self):
        self.client.close()
        self._connected = False

    def is_connected(self) -> bool:
        return self._connected

    def read_holding_registers(self, address: int, count: int = 1):
        if not self._connected:
            return None
        result = self.client.read_holding_registers(address, count, slave=self.unit_id)
        if result.isError():
            logger.warning(f"Modbus read error at {address}")
            return None
        return result.registers

    def read_coils(self, address: int, count: int = 1):
        if not self._connected:
            return None
        result = self.client.read_coils(address, count, slave=self.unit_id)
        if result.isError():
            return None
        return result.bits
```

### 4. `edge/agent/collectors/modbus/mapper.py`

```python
"""Tag mapping: Modbus register address → PlantOS signal_id."""

import struct


class TagMapper:
    def __init__(self, tags: list[dict]):
        self.tags = tags
        # Group by register type for batch reading
        self.holding_tags = [t for t in tags if t.get("type") == "holding"]
        self.coil_tags = [t for t in tags if t.get("type") == "coil"]

    def get_holding_registers(self) -> list[int]:
        return [t["register"] for t in self.holding_tags]

    def get_coil_addresses(self) -> list[int]:
        return [t["register"] for t in self.coil_tags]

    def map_holding_values(self, registers: list[int], start_addr: int) -> list[dict]:
        """Map raw register values to measurements using tag definitions."""
        results = []
        for tag in self.holding_tags:
            offset = tag["register"] - start_addr
            if 0 <= offset < len(registers):
                raw = registers[offset]
                if tag.get("data_type") == "float" and offset + 1 < len(registers):
                    # Combine 2 registers for float32
                    raw_bytes = struct.pack(">HH", registers[offset], registers[offset + 1])
                    value = struct.unpack(">f", raw_bytes)[0]
                else:
                    value = float(raw)
                value = value * tag.get("scale", 1.0) + tag.get("offset", 0.0)
                results.append({
                    "signal_id": tag["signal_id"],
                    "value": round(value, 3),
                })
        return results

    def map_coil_values(self, bits: list[bool], start_addr: int) -> list[dict]:
        results = []
        for tag in self.coil_tags:
            offset = tag["register"] - start_addr
            if 0 <= offset < len(bits):
                results.append({
                    "signal_id": tag["signal_id"],
                    "value": bits[offset],
                })
        return results
```

### 5. `edge/agent/collectors/modbus/collector.py`

```python
"""Modbus collector — poll registers, normalize, write to DuckDB."""

import asyncio
import logging
from datetime import datetime, timezone
from .client import ModbusClient
from .mapper import TagMapper

logger = logging.getLogger(__name__)


class ModbusCollector:
    def __init__(self, config: dict, buffer):
        self.config = config
        self.buffer = buffer
        self.client = ModbusClient(
            host=config.get("host", "127.0.0.1"),
            port=config.get("port", 502),
            unit_id=config.get("unit_id", 1),
        )
        self.mapper = TagMapper(config.get("tags", []))
        self.interval = config.get("poll_interval_ms", 1000) / 1000
        self._enabled = config.get("enabled", False)

    @property
    def connected(self) -> bool:
        return self.client.is_connected()

    async def start(self):
        if not self._enabled:
            logger.info("Modbus collector disabled")
            return

        if not self.client.connect():
            logger.warning("Modbus collector: connection failed, retrying...")
            # Retry in background
            asyncio.create_task(self._retry_connect())
            return

        logger.info(f"Modbus collector started ({len(self.mapper.tags)} tags)")
        asyncio.create_task(self._poll_loop())

    async def _retry_connect(self):
        while not self.client.is_connected():
            await asyncio.sleep(10)
            self.client.connect()

    async def _poll_loop(self):
        while self.client.is_connected():
            try:
                measurements = []

                # Read holding registers in batch
                if self.mapper.holding_tags:
                    addrs = self.mapper.get_holding_registers()
                    min_addr = min(addrs)
                    max_addr = max(addrs) + 1  # +1 extra for float32 pairs
                    regs = self.client.read_holding_registers(min_addr, max_addr - min_addr)
                    if regs:
                        measurements.extend(self.mapper.map_holding_values(regs, min_addr))

                # Read coils in batch
                if self.mapper.coil_tags:
                    addrs = self.mapper.get_coil_addresses()
                    min_addr = min(addrs)
                    max_addr = max(addrs) + 1
                    bits = self.client.read_coils(min_addr, max_addr - min_addr)
                    if bits:
                        measurements.extend(self.mapper.map_coil_values(bits, min_addr))

                # Write to local buffer
                if measurements:
                    now = datetime.now(timezone.utc)
                    rows = [
                        {"timestamp": now.isoformat(), "signal_id": m["signal_id"],
                         "value": m["value"], "quality": "GOOD", "source": "modbus"}
                        for m in measurements
                    ]
                    self.buffer.write(rows)

            except Exception as e:
                logger.error(f"Modbus poll error: {e}")

            await asyncio.sleep(self.interval)

    async def stop(self):
        self.client.disconnect()
```

### 6. `edge/agent/web.py` — Add Protocol Routes

```python
# In create_app(), add routes:
app.router.add_get("/setup", handle_setup_page)
app.router.add_get("/api/protocols/status", handle_protocol_status)

# Reference to modbus collector (set by main.py)
_modbus_collector = None

def set_modbus_collector(collector):
    global _modbus_collector
    _modbus_collector = collector


async def handle_protocol_status(request):
    """Return protocol connection status."""
    return web.json_response({
        "modbus": {
            "enabled": _modbus_collector is not None,
            "connected": _modbus_collector.connected if _modbus_collector else False,
            "host": _modbus_collector.config.get("host") if _modbus_collector else None,
            "tags": len(_modbus_collector.mapper.tags) if _modbus_collector else 0,
        }
    })


async def handle_setup_page(request):
    """Serve protocol setup page."""
    return web.FileResponse("templates/setup.html")
```

### 7. `edge/agent/templates/setup.html` — Protocol Setup Page

Inline HTML với form cấu hình Modbus: host, port, unit ID, poll interval, tag mapping table. Có nút "Test Connection" và "Save Config".

> Coder tự viết HTML form — pattern giống dashboard.html (inline, vanilla JS). Form gồm: input host/port/unit/poll, table tag mapping với register/type/signal columns, nút Test Connection gọi API.

### 8. `edge/agent/main.py` — Integrate

```python
from collectors.modbus.collector import ModbusCollector
from web import set_modbus_collector

# In EdgeAgent.__init__:
modbus_cfg = self.cfg.get("modbus", {})
self.modbus = ModbusCollector(modbus_cfg, self.buffer)
set_modbus_collector(self.modbus)

# In EdgeAgent.run():
asyncio.create_task(self.modbus.start())
```

## Constraints

- [x] Modbus collector chạy trên cùng event loop với agent
- [x] Tag mapping configurable qua YAML config
- [x] Batch read registers để tối ưu (1 request cho nhiều register)
- [x] Float32: tự động combine 2 holding registers
- [x] Graceful: retry connect mỗi 10s nếu mất kết nối

## Validation

```bash
# 1. Start edge agent
cd edge/agent && python main.py

# 2. Open setup page
open http://localhost:8001/setup

# 3. Check protocol status
curl http://localhost:8001/api/protocols/status

# 4. If Modbus device available, verify measurements flow
curl http://localhost:8001/api/measurements/latest
```
