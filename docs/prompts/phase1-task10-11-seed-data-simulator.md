# Phase 1 — Task 10-11: Demo Plant Seed Data + Edge Simulator (Gộp)

> **Designer:** DeepSeek V4 Pro | **Date:** 2026-06-30
> **Reason for merge:** Seed data là input của simulator. Gộp test được end-to-end: seed → publish → ingest → query.

## Context

Tạo demo plant scenario hoàn chỉnh: 1 plant, 2 areas, 7 assets, ~10 signals. Script seed data gọi API để tạo. Edge Simulator đọc config từ YAML và publish measurement liên tục qua HTTP.

Scenario theo `docs/18-edge-simulator-design.md` và `docs/12-mvp-scope.md` §4-7.

## Plan Reference

- `docs/18-edge-simulator-design.md` — Simulator goals, signal patterns, config
- `docs/12-mvp-scope.md` §4-7 — Demo plant assets + signals
- `docs/14-api-contract-mvp.md` §6 — Measurement ingest contract
- `docs/20-data-model.md` §3 — Asset/Signal canonical objects

## Demo Plant Scenario

```text
DEMO-PLANT
├── PROCESS-AREA
│   └── LINE-01 (parent asset)
│       ├── PUMP-101
│       │   ├── discharge_pressure  (float, bar)
│       │   ├── flow_rate           (float, m³/h)
│       │   ├── running_status      (bool)
│       │   └── vibration_rms       (float, mm/s)
│       ├── MOTOR-101
│       │   ├── motor_current       (float, A)
│       │   ├── motor_temperature   (float, °C)
│       │   └── running_status      (bool)
│       ├── TANK-101
│       │   ├── tank_level          (float, %)
│       │   └── temperature         (float, °C)
│       └── VALVE-101
│           └── valve_position      (float, %)
└── ELECTRICAL-AREA
    └── SUBSTATION-A
        ├── TRANSFORMER-01
        │   └── temperature         (float, °C)
        ├── FEEDER-01
        │   ├── current             (float, A)
        │   └── power               (float, kW)
        └── BREAKER-01
            ├── breaker_status      (bool)
            └── voltage             (float, kV)
```

## Implementation Checklist

- [ ] CREATE `scripts/seed_demo_plant.py` — Seed script gọi API
- [ ] CREATE `examples/demo-plant/demo-plant.yaml` — Simulator config
- [ ] CREATE `edge/simulator/simulator.py` — Simulator main script
- [ ] CREATE `edge/simulator/__init__.py` — Package marker
- [ ] CREATE `edge/simulator/requirements.txt` — Dependencies (httpx, pyyaml)
- [ ] MODIFY `edge/README.md` — How to run simulator
- [ ] VERIFY: run seed → run simulator → query data

## Detailed Instructions

### 1. `scripts/seed_demo_plant.py`

Script Python gọi API backend để tạo toàn bộ demo plant. Chạy: `python scripts/seed_demo_plant.py [--api-url http://localhost:8000]`

```python
#!/usr/bin/env python3
"""Seed DEMO-PLANT data into PlantOS via API."""

import argparse
import sys
import httpx

API = "http://localhost:8000/api/v1"


def post(path, data):
    resp = httpx.post(f"{API}{path}", json=data)
    if resp.status_code not in (200, 201):
        print(f"  FAIL {path}: {resp.status_code} {resp.text}")
        sys.exit(1)
    return resp.json()


def seed(api_url):
    global API
    API = api_url.rstrip("/") + "/api/v1"

    print("Seeding DEMO-PLANT...")

    # 1. Plant
    print("  Creating plant...")
    post("/plants", {"plant_id": "DEMO-PLANT", "name": "Demo Plant", "timezone": "Asia/Ho_Chi_Minh"})

    # 2. Areas
    print("  Creating areas...")
    post("/areas", {"area_id": "PROCESS-AREA", "plant_id": "DEMO-PLANT", "name": "Process Area"})
    post("/areas", {"area_id": "ELECTRICAL-AREA", "plant_id": "DEMO-PLANT", "name": "Electrical Area"})

    # 3. Assets
    print("  Creating assets...")
    # Line hierarchy
    post("/assets", {"asset_id": "LINE-01", "name": "Production Line 01", "asset_type": "line", "area_id": "PROCESS-AREA"})
    # Process assets
    post("/assets", {"asset_id": "PUMP-101", "name": "Feed Pump 101", "asset_type": "pump", "area_id": "PROCESS-AREA", "parent_asset_id": "LINE-01", "criticality": "high", "location": {"lat": 10.7626, "lng": 106.6602}})
    post("/assets", {"asset_id": "MOTOR-101", "name": "Drive Motor 101", "asset_type": "motor", "area_id": "PROCESS-AREA", "parent_asset_id": "LINE-01", "criticality": "high"})
    post("/assets", {"asset_id": "TANK-101", "name": "Storage Tank 101", "asset_type": "tank", "area_id": "PROCESS-AREA", "parent_asset_id": "LINE-01"})
    post("/assets", {"asset_id": "VALVE-101", "name": "Control Valve 101", "asset_type": "valve", "area_id": "PROCESS-AREA", "parent_asset_id": "LINE-01"})
    # Electrical assets
    post("/assets", {"asset_id": "SUBSTATION-A", "name": "Substation A", "asset_type": "substation", "area_id": "ELECTRICAL-AREA"})
    post("/assets", {"asset_id": "TRANSFORMER-01", "name": "Transformer 01", "asset_type": "transformer", "area_id": "ELECTRICAL-AREA", "parent_asset_id": "SUBSTATION-A", "criticality": "critical"})
    post("/assets", {"asset_id": "FEEDER-01", "name": "Feeder 01", "asset_type": "feeder", "area_id": "ELECTRICAL-AREA", "parent_asset_id": "SUBSTATION-A"})
    post("/assets", {"asset_id": "BREAKER-01", "name": "Breaker 01", "asset_type": "breaker", "area_id": "ELECTRICAL-AREA", "parent_asset_id": "SUBSTATION-A"})

    # 4. Signals
    print("  Creating signals...")
    signals = [
        # PUMP-101
        ("PUMP-101.discharge_pressure", "PUMP-101", "discharge_pressure", "Discharge Pressure", "bar", "float"),
        ("PUMP-101.flow_rate", "PUMP-101", "flow_rate", "Flow Rate", "m³/h", "float"),
        ("PUMP-101.running_status", "PUMP-101", "running_status", "Running Status", None, "bool"),
        ("PUMP-101.vibration_rms", "PUMP-101", "vibration_rms", "Vibration RMS", "mm/s", "float"),
        # MOTOR-101
        ("MOTOR-101.motor_current", "MOTOR-101", "motor_current", "Motor Current", "A", "float"),
        ("MOTOR-101.motor_temperature", "MOTOR-101", "motor_temperature", "Motor Temperature", "°C", "float"),
        ("MOTOR-101.running_status", "MOTOR-101", "running_status", "Running Status", None, "bool"),
        # TANK-101
        ("TANK-101.tank_level", "TANK-101", "tank_level", "Tank Level", "%", "float"),
        ("TANK-101.temperature", "TANK-101", "temperature", "Temperature", "°C", "float"),
        # VALVE-101
        ("VALVE-101.valve_position", "VALVE-101", "valve_position", "Valve Position", "%", "float"),
        # TRANSFORMER-01
        ("TRANSFORMER-01.temperature", "TRANSFORMER-01", "temperature", "Temperature", "°C", "float"),
        # FEEDER-01
        ("FEEDER-01.current", "FEEDER-01", "current", "Current", "A", "float"),
        ("FEEDER-01.power", "FEEDER-01", "power", "Active Power", "kW", "float"),
        # BREAKER-01
        ("BREAKER-01.breaker_status", "BREAKER-01", "breaker_status", "Breaker Status", None, "bool"),
        ("BREAKER-01.voltage", "BREAKER-01", "voltage", "Voltage", "kV", "float"),
    ]
    for sig_id, asset_id, name, display, unit, dtype in signals:
        body = {
            "signal_id": sig_id,
            "asset_id": asset_id,
            "signal_name": name,
            "display_name": display,
            "data_type": dtype,
            "signal_type": "measurement" if dtype == "float" else "status",
        }
        if unit:
            body["engineering_unit"] = unit
        body["source"] = {
            "source_type": "simulator",
            "source_ref": f"sim://{sig_id.replace('.', '/')}"
        }
        body["uns_path"] = f"avenue/demo-plant/{asset_id}/{name}"
        post("/signals", body)

    print(f"  Done! Created 1 plant, 2 areas, 9 assets, {len(signals)} signals.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed DEMO-PLANT data")
    parser.add_argument("--api-url", default="http://localhost:8000", help="Backend API URL")
    args = parser.parse_args()
    seed(args.api_url)
```

### 2. `examples/demo-plant/demo-plant.yaml`

```yaml
# Demo Plant Configuration for Edge Simulator
# See docs/18-edge-simulator-design.md

plant: DEMO-PLANT
edge_node_id: edge-sim-01

publish:
  mode: http
  url: http://localhost:8000/api/v1/measurements/ingest
  interval_seconds: 1
  batch_size: 10

scenario: normal_operation  # normal_operation | pump_high_pressure | motor_high_temperature | breaker_trip

signals:
  # PUMP-101 — Process
  - signal_id: PUMP-101.discharge_pressure
    data_type: float
    min: 5.0
    max: 9.0
    noise: 0.2
    pattern: sine  # sine | random_walk | step

  - signal_id: PUMP-101.flow_rate
    data_type: float
    min: 80.0
    max: 120.0
    noise: 1.0
    pattern: sine

  - signal_id: PUMP-101.running_status
    data_type: bool
    pattern: steady
    steady_value: true

  - signal_id: PUMP-101.vibration_rms
    data_type: float
    min: 1.0
    max: 3.0
    noise: 0.1
    pattern: random_walk

  # MOTOR-101
  - signal_id: MOTOR-101.motor_current
    data_type: float
    min: 40.0
    max: 60.0
    noise: 0.5
    pattern: sine

  - signal_id: MOTOR-101.motor_temperature
    data_type: float
    min: 50.0
    max: 70.0
    noise: 0.3
    pattern: random_walk

  - signal_id: MOTOR-101.running_status
    data_type: bool
    pattern: steady
    steady_value: true

  # TANK-101
  - signal_id: TANK-101.tank_level
    data_type: float
    min: 20.0
    max: 80.0
    noise: 0.5
    pattern: random_walk

  - signal_id: TANK-101.temperature
    data_type: float
    min: 20.0
    max: 30.0
    noise: 0.1
    pattern: sine

  # VALVE-101
  - signal_id: VALVE-101.valve_position
    data_type: float
    min: 0.0
    max: 100.0
    noise: 2.0
    pattern: step
    step_values: [45.0, 60.0, 75.0]
    step_interval: 30  # seconds

  # TRANSFORMER-01
  - signal_id: TRANSFORMER-01.temperature
    data_type: float
    min: 40.0
    max: 65.0
    noise: 0.2
    pattern: random_walk

  # FEEDER-01
  - signal_id: FEEDER-01.current
    data_type: float
    min: 100.0
    max: 200.0
    noise: 2.0
    pattern: sine

  - signal_id: FEEDER-01.power
    data_type: float
    min: 20.0
    max: 50.0
    noise: 1.0
    pattern: sine

  # BREAKER-01
  - signal_id: BREAKER-01.breaker_status
    data_type: bool
    pattern: steady
    steady_value: true

  - signal_id: BREAKER-01.voltage
    data_type: float
    min: 21.0
    max: 23.0
    noise: 0.05
    pattern: sine

scenarios:
  normal_operation: {}
  pump_high_pressure:
    PUMP-101.discharge_pressure:
      min: 9.0
      max: 14.0
      noise: 0.5
  motor_high_temperature:
    MOTOR-101.motor_temperature:
      min: 75.0
      max: 95.0
      noise: 0.8
  breaker_trip:
    BREAKER-01.breaker_status:
      pattern: step
      step_values: [true, false]
      step_interval: 60
```

### 3. `edge/simulator/simulator.py`

Script chính của simulator. Đọc YAML config, generate data, publish.

```python
#!/usr/bin/env python3
"""PlantOS Edge Simulator — generates demo plant telemetry and publishes via HTTP."""

import argparse
import asyncio
import math
import random
import sys
from datetime import datetime, timezone
from pathlib import Path

import httpx
import yaml


class SignalGenerator:
    """Generate realistic time-series values for a signal."""

    def __init__(self, cfg: dict):
        self.signal_id = cfg["signal_id"]
        self.data_type = cfg.get("data_type", "float")
        self.v_min = cfg.get("min", 0.0)
        self.v_max = cfg.get("max", 100.0)
        self.noise = cfg.get("noise", 0.1)
        self.pattern = cfg.get("pattern", "sine")
        self.steady_value = cfg.get("steady_value", None)
        self.step_values = cfg.get("step_values", [])
        self.step_interval = cfg.get("step_interval", 10)
        self._phase = random.uniform(0, 2 * math.pi)
        self._value = random.uniform(self.v_min, self.v_max)
        self._step_idx = 0
        self._step_counter = 0

    def update(self, elapsed_seconds: float):
        mid = (self.v_min + self.v_max) / 2
        amp = (self.v_max - self.v_min) / 2

        if self.pattern == "sine":
            self._phase += elapsed_seconds * 0.1
            self._value = mid + amp * math.sin(self._phase)
        elif self.pattern == "random_walk":
            self._value += random.gauss(0, self.noise * elapsed_seconds)
            self._value = max(self.v_min, min(self.v_max, self._value))
        elif self.pattern == "steady":
            self._value = self.steady_value if self.steady_value is not None else mid
        elif self.pattern == "step":
            self._step_counter += 1
            if self._step_counter >= self.step_interval:
                self._step_counter = 0
                self._step_idx = (self._step_idx + 1) % len(self.step_values)
                self._value = self.step_values[self._step_idx]

        # Add noise
        if self.data_type == "float":
            self._value += random.gauss(0, self.noise)
        return self._value

    def get_value(self):
        if self.data_type == "bool":
            return bool(self._value) if isinstance(self._value, (int, float)) else self._value
        return round(self._value, 3)


class Simulator:
    def __init__(self, config_path: str):
        with open(config_path) as f:
            self.config = yaml.safe_load(f)

        self.edge_node_id = self.config["edge_node_id"]
        self.publish_url = self.config["publish"]["url"]
        self.interval = self.config["publish"]["interval_seconds"]
        self.batch_size = self.config["publish"].get("batch_size", 10)
        self.scenario = self.config.get("scenario", "normal_operation")

        # Apply scenario overrides
        scenario_overrides = self.config.get("scenarios", {}).get(self.scenario, {})
        self.generators = []
        for sig_cfg in self.config["signals"]:
            sig_id = sig_cfg["signal_id"]
            effective = dict(sig_cfg)
            if sig_id in scenario_overrides:
                effective.update(scenario_overrides[sig_id])
            self.generators.append(SignalGenerator(effective))

        self._elapsed = 0.0
        print(f"Simulator loaded: {len(self.generators)} signals, scenario={self.scenario}")

    async def run(self, duration_seconds: float = 0):
        """Run the simulation loop. duration=0 means run forever."""
        start = datetime.now(timezone.utc)
        print(f"Publishing to {self.publish_url} every {self.interval}s")

        async with httpx.AsyncClient(timeout=10) as client:
            while True:
                # Generate measurements
                measurements = []
                now = datetime.now(timezone.utc)
                for gen in self.generators:
                    value = gen.update(self.interval)
                    measurements.append({
                        "timestamp": now.isoformat(),
                        "signal_id": gen.signal_id,
                        "value": gen.get_value(),
                        "quality": "SIMULATED",
                    })

                # Publish in batches
                for i in range(0, len(measurements), self.batch_size):
                    batch = measurements[i:i + self.batch_size]
                    try:
                        resp = await client.post(self.publish_url, json={
                            "source": self.edge_node_id,
                            "measurements": batch,
                        })
                        if resp.status_code not in (200, 201):
                            print(f"  Publish error: {resp.status_code}")
                    except Exception as e:
                        print(f"  Connection error: {e}")

                self._elapsed += self.interval
                print(f"  [{self._elapsed:.0f}s] Published {len(measurements)} measurements", end="\r")

                if duration_seconds > 0 and self._elapsed >= duration_seconds:
                    break

                await asyncio.sleep(self.interval)

        print(f"\nDone. Ran for {self._elapsed:.0f}s")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PlantOS Edge Simulator")
    parser.add_argument("--config", default="examples/demo-plant/demo-plant.yaml", help="Config file path")
    parser.add_argument("--duration", type=float, default=0, help="Duration in seconds (0=forever)")
    parser.add_argument("--scenario", default=None, help="Override scenario (normal_operation, pump_high_pressure, etc.)")
    args = parser.parse_args()

    sim = Simulator(args.config)
    if args.scenario:
        sim.scenario = args.scenario

    asyncio.run(sim.run(args.duration))
```

### 4. `edge/simulator/__init__.py`

```python
# Edge Simulator package
```

### 5. `edge/simulator/requirements.txt`

```
httpx>=0.28.0
pyyaml>=6.0
```

### 6. `edge/README.md` — Update

Thêm section:

```markdown
## Running the Simulator

```bash
# 1. Seed demo plant data (backend must be running)
cd ..
python scripts/seed_demo_plant.py --api-url http://localhost:8000

# 2. Start simulator
cd edge/simulator
pip install -r requirements.txt
python simulator.py --config ../../examples/demo-plant/demo-plant.yaml

# 3. Try different scenarios
python simulator.py --scenario pump_high_pressure --duration 30
python simulator.py --scenario breaker_trip --duration 30

# 4. Query ingested data
curl "http://localhost:8000/api/v1/measurements/current?asset_id=PUMP-101"
```
```

## Constraints

- [x] Simulator publishes qua HTTP API (không bypass API gọi thẳng TDengine)
- [x] Seed data dùng API endpoints đã có (không INSERT thẳng PostgreSQL)
- [x] Simulator dùng canonical measurement format (timestamp, signal_id, value, quality, source)
- [x] Quality = "SIMULATED" cho tất cả values
- [x] Không hardcode asset/signal trong code generator (đọc từ YAML)

## Validation

```bash
# 1. Start backend
cd backend && uvicorn app.main:app --port 8000 &

# 2. Seed data
python scripts/seed_demo_plant.py

# 3. Verify seed
curl http://localhost:8000/api/v1/assets | python -m json.tool | head -20
curl http://localhost:8000/api/v1/signals | python -m json.tool | head -20

# 4. Run simulator 10s
cd edge/simulator
pip install -r requirements.txt
python simulator.py --duration 10

# 5. Query current values
curl "http://localhost:8000/api/v1/measurements/current?asset_id=PUMP-101"

# 6. Query history
curl "http://localhost:8000/api/v1/measurements/history?signal_id=PUMP-101.discharge_pressure&from=2026-06-30T00:00:00&to=2026-06-30T23:59:59"
```

## Expected Output Format

```
Standard — như các task trước.
Đặc biệt: xác nhận end-to-end flow hoạt động:
  seed → simulator publish → ingest → query returned data.
```
