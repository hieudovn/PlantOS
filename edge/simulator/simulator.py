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
