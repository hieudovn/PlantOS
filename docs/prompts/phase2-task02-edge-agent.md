# Phase 2 — Task 2-02: Edge Agent Foundation (DuckDB + MQTT + Store-and-Forward)

> **Designer:** DeepSeek V4 Pro | **Date:** 2026-06-30

## Context

Xây dựng Edge Agent foundation: DuckDB local buffer, MQTT publish qua EMQX, store-and-forward khi mất kết nối, health reporting, và Edge Fleet UI.

Kiến trúc theo `docs/60-edge-center-strategy.md` và `docs/adr/ADR-0003-edge-local-tsdb-duckdb.md`.

## Architecture

```
Edge Agent (Python)
├── buffer.py       → DuckDB write/query/retention
├── publisher.py    → MQTT publish qua EMQX (per UNS topic)
├── sync.py         → Store-and-forward: detect offline → flush khi reconnect
├── health.py       → Heartbeat POST đến Center
├── config.yaml     → Signal list, intervals, MQTT broker
└── main.py         → Coordinator: collector → buffer → publish → sync

Center
├── EMQX            → Nhận MQTT messages
├── Backend API     → /api/v1/edge-nodes/heartbeat
└── Edge Fleet UI   → Replace 🚧 with real data
```

## Implementation Checklist

- [ ] CREATE `edge/agent/requirements.txt` — duckdb, httpx, paho-mqtt, pyyaml
- [ ] CREATE `edge/agent/config.yaml` — Edge agent configuration
- [ ] CREATE `edge/agent/buffer.py` — DuckDB local time-series storage
- [ ] CREATE `edge/agent/publisher.py` — MQTT publisher (EMQX)
- [ ] CREATE `edge/agent/sync.py` — Store-and-forward logic
- [ ] CREATE `edge/agent/health.py` — Heartbeat reporter
- [ ] CREATE `edge/agent/main.py` — Agent coordinator
- [ ] CREATE `backend/app/modules/edge_nodes/router.py` — Heartbeat API endpoint
- [ ] CREATE `backend/app/modules/edge_nodes/service.py` — Edge node service
- [ ] MODIFY `backend/app/api/v1.py` — include edge_nodes router
- [ ] CREATE `frontend/src/features/edge-fleet/EdgeFleetPage.tsx` — Replace 🚧
- [ ] MODIFY `frontend/src/routes/index.tsx` — Replace placeholder

## Detailed Instructions

### 1. `edge/agent/requirements.txt`

```
duckdb>=1.0.0
httpx>=0.28.0
paho-mqtt>=2.0.0
pyyaml>=6.0
```

### 2. `edge/agent/config.yaml`

```yaml
edge_node_id: edge-agent-01
plant_id: DEMO-PLANT

# DuckDB local buffer
buffer:
  path: edge_data.duckdb
  retention_days: 60

# MQTT publisher
mqtt:
  host: localhost
  port: 1883
  topic_prefix: avenue/demo-plant

# HTTP fallback (when MQTT unavailable)
http:
  ingest_url: http://localhost:8000/api/v1/measurements/ingest

# Center heartbeat
heartbeat:
  url: http://localhost:8000/api/v1/edge-nodes/heartbeat
  interval_seconds: 10

# Signal generation (same signals as simulator)
signals:
  - signal_id: PUMP-101.discharge_pressure
    data_type: float
    min: 5.0
    max: 9.0
    noise: 0.2
    pattern: sine
  - signal_id: PUMP-101.flow_rate
    data_type: float
    min: 80.0
    max: 120.0
    noise: 1.0
    pattern: sine
  - signal_id: MOTOR-101.motor_current
    data_type: float
    min: 40.0
    max: 60.0
    noise: 0.5
    pattern: sine

publish:
  interval_seconds: 1
  batch_size: 10
```

### 3. `edge/agent/buffer.py` — DuckDB Storage

```python
"""DuckDB local time-series buffer — per ADR-0003."""

import duckdb
from datetime import datetime, timedelta, timezone


class DuckDBBuffer:
    def __init__(self, path: str = "edge_data.duckdb", retention_days: int = 60):
        self.path = path
        self.retention_days = retention_days
        self.conn = duckdb.connect(path)
        self._init_schema()

    def _init_schema(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS measurements (
                ts          TIMESTAMPTZ NOT NULL,
                signal_id   VARCHAR NOT NULL,
                value       DOUBLE,
                quality     VARCHAR,
                source      VARCHAR,
                synced      BOOLEAN DEFAULT FALSE
            )
        """)
        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_meas_signal_ts
            ON measurements(signal_id, ts)
        """)

    def write(self, measurements: list[dict]):
        """Write batch of measurements to local buffer."""
        for m in measurements:
            self.conn.execute("""
                INSERT INTO measurements (ts, signal_id, value, quality, source, synced)
                VALUES (?, ?, ?, ?, ?, FALSE)
            """, [m["timestamp"], m["signal_id"], m["value"], m.get("quality", "GOOD"), m.get("source", "edge")])

    def get_unsynced(self, limit: int = 1000) -> list[dict]:
        """Get measurements not yet synced to Center."""
        rows = self.conn.execute("""
            SELECT ts, signal_id, value, quality, source
            FROM measurements WHERE synced = FALSE
            ORDER BY ts ASC LIMIT ?
        """, [limit]).fetchall()
        return [
            {"timestamp": r[0].isoformat(), "signal_id": r[1], "value": r[2], "quality": r[3], "source": r[4]}
            for r in rows
        ]

    def mark_synced(self, count: int):
        """Mark oldest N unsynced rows as synced."""
        self.conn.execute("""
            UPDATE measurements SET synced = TRUE
            WHERE rowid IN (
                SELECT rowid FROM measurements WHERE synced = FALSE
                ORDER BY ts ASC LIMIT ?
            )
        """, [count])

    def cleanup_retention(self):
        """Delete data older than retention period."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=self.retention_days)
        self.conn.execute("DELETE FROM measurements WHERE ts < ?", [cutoff.isoformat()])

    def count_unsynced(self) -> int:
        return self.conn.execute("SELECT COUNT(*) FROM measurements WHERE synced = FALSE").fetchone()[0]

    def close(self):
        self.conn.close()
```

### 4. `edge/agent/publisher.py` — MQTT Publisher

```python
"""MQTT publisher — sends measurements to EMQX per UNS topic."""

import json
import logging
import paho.mqtt.client as mqtt

logger = logging.getLogger(__name__)


class MQTTPublisher:
    def __init__(self, host: str, port: int, topic_prefix: str, edge_node_id: str):
        self.topic_prefix = topic_prefix
        self.edge_node_id = edge_node_id
        self.client = mqtt.Client(client_id=edge_node_id)
        self.client.on_connect = self._on_connect
        self.connected = False

        try:
            self.client.connect(host, port, keepalive=30)
            self.client.loop_start()
            logger.info(f"MQTT connecting to {host}:{port}")
        except Exception as e:
            logger.warning(f"MQTT connect failed: {e}")

    def _on_connect(self, client, userdata, flags, rc):
        self.connected = rc == 0
        if self.connected:
            logger.info("MQTT connected")
        else:
            logger.warning(f"MQTT connection failed: rc={rc}")

    def publish_measurements(self, measurements: list[dict]):
        """Publish batch to MQTT. Topic: {prefix}/{signal_id}"""
        if not self.connected:
            return False

        for m in measurements:
            topic = f"{self.topic_prefix}/{m['signal_id'].replace('.', '/')}"
            payload = json.dumps({
                "timestamp": m["timestamp"],
                "value": m["value"],
                "quality": m.get("quality", "GOOD"),
                "source": self.edge_node_id,
            })
            self.client.publish(topic, payload, qos=1)

        return True

    def is_connected(self) -> bool:
        return self.connected

    def stop(self):
        self.client.loop_stop()
        self.client.disconnect()
```

### 5. `edge/agent/sync.py` — Store-and-Forward

```python
"""Store-and-Forward — sync buffered data to Center when connected."""

import logging
import httpx

logger = logging.getLogger(__name__)


class StoreAndForward:
    def __init__(self, buffer, ingest_url: str, edge_node_id: str):
        self.buffer = buffer
        self.ingest_url = ingest_url
        self.edge_node_id = edge_node_id

    async def flush(self, batch_size: int = 100) -> int:
        """Flush unsynced data to Center. Returns number of synced points."""
        unsynced = self.buffer.get_unsynced(batch_size)
        if not unsynced:
            return 0

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(self.ingest_url, json={
                    "source": self.edge_node_id,
                    "measurements": unsynced,
                })
                if resp.status_code in (200, 201):
                    data = resp.json()
                    synced = data.get("accepted", 0)
                    if synced > 0:
                        self.buffer.mark_synced(synced)
                    logger.info(f"Flushed {synced}/{len(unsynced)} measurements")
                    return synced
                else:
                    logger.warning(f"Flush failed: HTTP {resp.status_code}")
                    return 0
        except Exception as e:
            logger.warning(f"Flush error: {e}")
            return 0

    def get_backlog(self) -> int:
        return self.buffer.count_unsynced()
```

### 6. `edge/agent/health.py` — Heartbeat Reporter

```python
"""Heartbeat — report edge node health to Center."""

import logging
import asyncio
import httpx

logger = logging.getLogger(__name__)


class HealthReporter:
    def __init__(self, heartbeat_url: str, edge_node_id: str, interval: int = 10):
        self.url = heartbeat_url
        self.node_id = edge_node_id
        self.interval = interval

    async def send_heartbeat(self, status: str = "online", backlog: int = 0):
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                await client.post(self.url, json={
                    "edge_node_id": self.node_id,
                    "status": status,
                    "backlog_count": backlog,
                })
        except Exception as e:
            logger.warning(f"Heartbeat failed: {e}")

    async def run(self, get_backlog_fn):
        """Send heartbeats periodically."""
        while True:
            backlog = get_backlog_fn()
            await self.send_heartbeat("online", backlog)
            await asyncio.sleep(self.interval)
```

### 7. `edge/agent/main.py` — Agent Coordinator

```python
#!/usr/bin/env python3
"""PlantOS Edge Agent — collector → DuckDB buffer → MQTT publish → sync."""

import argparse
import asyncio
import logging
import math
import random
import yaml
from datetime import datetime, timezone
from pathlib import Path

from buffer import DuckDBBuffer
from publisher import MQTTPublisher
from sync import StoreAndForward
from health import HealthReporter

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s")
logger = logging.getLogger("edge-agent")


class SignalGenerator:
    """Simple signal generator (same pattern as simulator)."""

    def __init__(self, cfg: dict):
        self.signal_id = cfg["signal_id"]
        self.v_min = cfg.get("min", 0)
        self.v_max = cfg.get("max", 100)
        self.noise = cfg.get("noise", 0.1)
        self.pattern = cfg.get("pattern", "sine")
        self._phase = random.uniform(0, 2 * math.pi)
        self._value = random.uniform(self.v_min, self.v_max)

    def update(self, dt: float) -> float:
        mid = (self.v_min + self.v_max) / 2
        amp = (self.v_max - self.v_min) / 2
        if self.pattern == "sine":
            self._phase += dt * 0.1
            self._value = mid + amp * math.sin(self._phase)
        elif self.pattern == "random_walk":
            self._value += random.gauss(0, self.noise * dt)
            self._value = max(self.v_min, min(self.v_max, self._value))
        self._value += random.gauss(0, self.noise)
        return round(self._value, 3)


class EdgeAgent:
    def __init__(self, config_path: str):
        with open(config_path) as f:
            self.cfg = yaml.safe_load(f)

        self.node_id = self.cfg["edge_node_id"]
        self.interval = self.cfg["publish"]["interval_seconds"]
        self.batch_size = self.cfg["publish"]["batch_size"]

        # DuckDB buffer
        self.buffer = DuckDBBuffer(
            path=self.cfg["buffer"]["path"],
            retention_days=self.cfg["buffer"]["retention_days"],
        )

        # MQTT publisher
        mqtt_cfg = self.cfg["mqtt"]
        self.mqtt = MQTTPublisher(mqtt_cfg["host"], mqtt_cfg["port"], mqtt_cfg["topic_prefix"], self.node_id)

        # Store-and-forward
        self.sync = StoreAndForward(self.buffer, self.cfg["http"]["ingest_url"], self.node_id)

        # Health reporter
        self.health = HealthReporter(self.cfg["heartbeat"]["url"], self.node_id, self.cfg["heartbeat"]["interval_seconds"])

        # Signal generators
        self.generators = [SignalGenerator(s) for s in self.cfg["signals"]]

        logger.info(f"Agent {self.node_id} started with {len(self.generators)} signals")

    async def run(self):
        asyncio.create_task(self.health.run(lambda: self.sync.get_backlog()))

        while True:
            # Generate measurements
            now = datetime.now(timezone.utc)
            measurements = []
            for gen in self.generators:
                val = gen.update(self.interval)
                measurements.append({
                    "timestamp": now.isoformat(),
                    "signal_id": gen.signal_id,
                    "value": val,
                    "quality": "SIMULATED",
                    "source": self.node_id,
                })

            # Write to DuckDB
            self.buffer.write(measurements)

            # Publish via MQTT
            self.mqtt.publish_measurements(measurements)

            # Sync backlog to Center via HTTP
            await self.sync.flush(self.batch_size)

            # Periodic retention cleanup (every 100 cycles ~ 100s)
            if random.randint(0, 99) == 0:
                self.buffer.cleanup_retention()

            await asyncio.sleep(self.interval)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PlantOS Edge Agent")
    parser.add_argument("--config", default="config.yaml")
    args = parser.parse_args()

    agent = EdgeAgent(args.config)
    try:
        asyncio.run(agent.run())
    except KeyboardInterrupt:
        logger.info("Agent stopped")
```

### 8. `backend/app/modules/edge_nodes/router.py` — Heartbeat API

```python
"""Edge Node — FastAPI router for heartbeat."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime, timezone

router = APIRouter()

# In-memory store for MVP (replace with PostgreSQL in production)
_edge_nodes: dict[str, dict] = {}


class HeartbeatRequest(BaseModel):
    edge_node_id: str
    status: str = "online"
    backlog_count: int = 0


@router.post("/edge-nodes/heartbeat")
def receive_heartbeat(data: HeartbeatRequest):
    """Receive heartbeat from edge node."""
    _edge_nodes[data.edge_node_id] = {
        "edge_node_id": data.edge_node_id,
        "status": data.status,
        "backlog_count": data.backlog_count,
        "last_heartbeat": datetime.now(timezone.utc).isoformat(),
    }
    return {"status": "ok"}


@router.get("/edge-nodes")
def list_edge_nodes():
    """List all known edge nodes."""
    return list(_edge_nodes.values())
```

### 9. Backend route integration

`backend/app/api/v1.py` — add:
```python
from app.modules.edge_nodes.router import router as edge_nodes_router
router.include_router(edge_nodes_router, tags=["Edge Nodes"])
```

### 10. `frontend/src/features/edge-fleet/EdgeFleetPage.tsx`

```tsx
import { useQuery } from "@tanstack/react-query";
import { StatusBadge } from "@/components/StatusBadge";

async function getEdgeNodes() {
  const res = await fetch("/api/v1/edge-nodes");
  if (!res.ok) throw new Error("Failed");
  return res.json();
}

export function EdgeFleetPage() {
  const { data: nodes, isLoading } = useQuery({
    queryKey: ["edge-nodes"],
    queryFn: getEdgeNodes,
    refetchInterval: 5000,
  });

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Edge Fleet</h1>
      {isLoading ? <div className="text-gray-500">Loading...</div> : (
        <div className="rounded-lg border border-gray-800 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-900 text-gray-400">
              <tr>
                <th className="text-left px-4 py-3">Node ID</th>
                <th className="text-left px-4 py-3">Status</th>
                <th className="text-left px-4 py-3">Backlog</th>
                <th className="text-left px-4 py-3">Last Heartbeat</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800">
              {nodes?.map((n: any) => (
                <tr key={n.edge_node_id}>
                  <td className="px-4 py-3 font-mono text-xs">{n.edge_node_id}</td>
                  <td className="px-4 py-3"><StatusBadge status={n.status} /></td>
                  <td className="px-4 py-3 text-gray-400">{n.backlog_count}</td>
                  <td className="px-4 py-3 text-gray-500 text-xs">{n.last_heartbeat ? new Date(n.last_heartbeat).toLocaleString() : "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
```

### 11. Replace 🚧 placeholder

```tsx
import { EdgeFleetPage } from "@/features/edge-fleet/EdgeFleetPage";
{ path: "edge", element: <EdgeFleetPage /> },
```

## Constraints

- [x] Edge Agent độc lập — chạy được không cần Center
- [x] DuckDB chỉ trên Edge — không dùng cho Center
- [x] MQTT topic theo UNS pattern: `avenue/{plant}/{area}/{asset}/{signal}`
- [x] Store-and-forward: buffer local → flush khi có kết nối
- [x] Heartbeat qua HTTP API, không MQTT (đơn giản hơn)

## Validation

```bash
# 1. Start EMQX
docker compose -f deployment/docker-compose.yml up -d emqx

# 2. Install deps & start agent
cd edge/agent
pip install -r requirements.txt
python main.py --config config.yaml

# 3. Open Edge Fleet page → verify node appears
open http://localhost:5173/edge

# 4. Check MQTT messages
# Use MQTT client to subscribe: avenue/demo-plant/#
```
