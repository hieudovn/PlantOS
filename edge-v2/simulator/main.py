#!/usr/bin/env python3
"""Edge v2 Simulator — basic sine wave signal generator.

Generates sine waves for 5 EDGEV2-DEMO assets × 7 signals total.
Configurable amplitude, frequency, and noise per signal.
Outputs to stdout in JSON lines format. Will be connected to DuckDB buffer
and MQTT publisher in E2V2-1.

Usage:
    python -m edge_v2.simulator.main [--interval 2.0] [--count 0]
"""

import argparse
import asyncio
import json
import math
import random
import sys
from datetime import datetime, timezone
from typing import Any


# Signal definitions per task spec: 5 assets, 7 signals total
SIGNAL_DEFINITIONS: list[dict[str, Any]] = [
    # PUMP-101: 3 signals
    {"asset": "EDGEV2-PUMP-101", "signal": "flow_rate",         "unit": "m³/h",  "min": 0,    "max": 100, "period": 12.0, "noise": 0.5},
    {"asset": "EDGEV2-PUMP-101", "signal": "discharge_pressure","unit": "bar",   "min": 0,    "max": 10,  "period": 8.0,  "noise": 0.1},
    {"asset": "EDGEV2-PUMP-101", "signal": "vibration",         "unit": "mm/s",  "min": 0,    "max": 20,  "period": 3.0,  "noise": 0.3},
    # TANK-101: 1 signal
    {"asset": "EDGEV2-TANK-101", "signal": "level",             "unit": "%",     "min": 0,    "max": 100, "period": 30.0, "noise": 1.0},
    # MOTOR-101: 1 signal
    {"asset": "EDGEV2-MOTOR-101","signal": "running_status",    "unit": "",      "min": 0,    "max": 1,   "period": 0,    "noise": 0},
    # QUALITY-STATION-101: 1 signal
    {"asset": "EDGEV2-QUALITY-STATION-101", "signal": "turbidity", "unit": "NTU", "min": 0,  "max": 50,  "period": 20.0, "noise": 0.8},
    # ENERGY-METER-101: 1 signal
    {"asset": "EDGEV2-ENERGY-METER-101", "signal": "active_power", "unit": "kW", "min": 0, "max": 500, "period": 15.0, "noise": 2.0},
]


class SineGenerator:
    """Per-signal sine wave generator with configurable noise."""

    def __init__(self, cfg: dict):
        self.asset = cfg["asset"]
        self.signal_name = cfg["signal"]
        self.signal_id = f"{self.asset}.{self.signal_name}"
        self.unit = cfg["unit"]
        self.min_val = cfg["min"]
        self.max_val = cfg["max"]
        self.period = cfg["period"]
        self.noise = cfg["noise"]
        self._phase = random.uniform(0, 2 * math.pi)
        self._last_binary_update = 0.0

    def generate(self, elapsed: float) -> dict:
        mid = (self.min_val + self.max_val) / 2
        amp = (self.max_val - self.min_val) / 2

        if self.period > 0:
            # Sine wave
            self._phase = elapsed * (2 * math.pi / self.period)
            value = mid + amp * math.sin(self._phase)
            value += random.gauss(0, self.noise)
        else:
            # Binary/square wave (for running_status)
            value = 1.0 if (int(elapsed) % 30) < 25 else 0.0

        value = max(self.min_val, min(self.max_val, value))
        value = round(value, 3)

        return {
            "signal_id": self.signal_id,
            "asset": self.asset,
            "signal_name": self.signal_name,
            "value": value,
            "unit": self.unit,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "quality": "GOOD",
        }


async def run_simulator(interval: float, count: int):
    """Run the simulator, outputting JSON lines to stdout.

    Args:
        interval: Seconds between generations (default 2.0)
        count: Number of cycles (0 = infinite)
    """
    generators = [SineGenerator(cfg) for cfg in SIGNAL_DEFINITIONS]
    elapsed = 0.0
    cycle = 0

    while count == 0 or cycle < count:
        readings = [g.generate(elapsed) for g in generators]

        # Output as JSON lines
        for r in readings:
            print(json.dumps(r), flush=True)

        elapsed += interval
        cycle += 1
        await asyncio.sleep(interval)


def main():
    parser = argparse.ArgumentParser(description="Edge v2 Simulator")
    parser.add_argument("--interval", type=float, default=2.0,
                        help="Generation interval in seconds (default: 2.0)")
    parser.add_argument("--count", type=int, default=0,
                        help="Number of cycles to run (0 = infinite, default: 0)")
    args = parser.parse_args()

    print(json.dumps({
        "event": "simulator.start",
        "assets": 5,
        "signals": 7,
        "interval": args.interval,
        "mode": "stdout",
    }), flush=True)

    asyncio.run(run_simulator(args.interval, args.count))


if __name__ == "__main__":
    main()
