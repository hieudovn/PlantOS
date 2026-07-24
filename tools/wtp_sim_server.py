#!/usr/bin/env python3
"""WTP Plant Simulator HTTP Server for Edge V2 HTTP Poll connector.

Generates dynamic sine/random_walk values for 19 WTP signals and serves them
as a flat JSON object on GET /.

Usage:
    python wtp_sim_server.py [--port 9998]

Edge V2 HTTP Poll connector hits GET / and extracts values by signal_id key.
"""

import argparse
import asyncio
import json
import math
import random
import signal
import sys
from datetime import datetime, timezone, timedelta
from typing import Any

from aiohttp import web

# Vietnam timezone UTC+7
VN_TZ = timezone(timedelta(hours=7))

# ── Signal definitions (matching Edge V2 config mirror_wtp_signals tags) ──

SIGNALS: list[dict[str, Any]] = [
    {"signal_id": "PUMP-101.flow_rate",              "min": 80,  "max": 120, "noise": 1.0, "pattern": "sine"},
    {"signal_id": "PUMP-101.discharge_pressure",      "min": 5.0, "max": 9.0,  "noise": 0.2, "pattern": "sine"},
    {"signal_id": "PUMP-101.running_status",          "min": 0,   "max": 1,    "noise": 0,   "pattern": "steady", "steady_value": 1},
    {"signal_id": "PUMP-101.vibration_rms",           "min": 1.0, "max": 3.0,  "noise": 0.1, "pattern": "random_walk"},
    {"signal_id": "MOTOR-101.motor_current",          "min": 40,  "max": 60,   "noise": 0.5, "pattern": "sine"},
    {"signal_id": "MOTOR-101.motor_temperature",      "min": 50,  "max": 70,   "noise": 0.3, "pattern": "random_walk"},
    {"signal_id": "MOTOR-101.running_status",         "min": 0,   "max": 1,    "noise": 0,   "pattern": "steady", "steady_value": 1},
    {"signal_id": "TANK-101.tank_level",              "min": 20,  "max": 80,   "noise": 0.5, "pattern": "random_walk"},
    {"signal_id": "TANK-101.temperature",             "min": 20,  "max": 30,   "noise": 0.1, "pattern": "sine"},
    {"signal_id": "RAW-WATER-QUALITY-STATION-101.raw_turbidity",   "min": 0, "max": 50, "noise": 0.8, "pattern": "random_walk"},
    {"signal_id": "RAW-WATER-QUALITY-STATION-101.raw_ph",          "min": 6.5, "max": 8.5, "noise": 0.05, "pattern": "sine"},
    {"signal_id": "RAW-WATER-QUALITY-STATION-101.raw_temperature", "min": 18, "max": 30, "noise": 0.2, "pattern": "sine"},
    {"signal_id": "FILTER-101.filter_dp",             "min": 0.5, "max": 2.0, "noise": 0.05, "pattern": "random_walk"},
    {"signal_id": "FILTER-101.effluent_flow",         "min": 70,  "max": 110,  "noise": 1.0, "pattern": "sine"},
    {"signal_id": "CLEAR-WATER-TANK-101.level",       "min": 30,  "max": 90,   "noise": 0.5, "pattern": "random_walk"},
    {"signal_id": "HSP-101.flow_rate",                "min": 60,  "max": 100,  "noise": 1.0, "pattern": "sine"},
    {"signal_id": "HSP-101-MOTOR.motor_current",      "min": 30,  "max": 50,   "noise": 0.5, "pattern": "sine"},
    {"signal_id": "COAG-PUMP-101.flow_rate",          "min": 0.5, "max": 2.0,  "noise": 0.05, "pattern": "random_walk"},
    {"signal_id": "CHLORINE-PUMP-101.flow_rate",      "min": 0.3, "max": 1.5,  "noise": 0.03, "pattern": "random_walk"},
]


class SignalGenerator:
    """Per-signal sine/random_walk/steady generator."""

    def __init__(self, cfg: dict):
        self.signal_id = cfg["signal_id"]
        self.v_min = cfg.get("min", 0.0)
        self.v_max = cfg.get("max", 100.0)
        self.noise = cfg.get("noise", 0.1)
        self.pattern = cfg.get("pattern", "sine")
        self.steady_value = cfg.get("steady_value", None)
        self._phase = random.uniform(0, 2 * math.pi)
        self._value = random.uniform(self.v_min, self.v_max)

    def update(self, elapsed_seconds: float = 1.0):
        mid = (self.v_min + self.v_max) / 2
        amp = (self.v_max - self.v_min) / 2

        if self.pattern == "sine":
            self._phase += elapsed_seconds * 0.1
            self._value = mid + amp * math.sin(self._phase)
        elif self.pattern == "random_walk":
            self._value += random.gauss(0, self.noise * elapsed_seconds)
            self._value = max(self.v_min, min(self.v_max, self._value))
        elif self.pattern == "steady":
            if self.steady_value is not None:
                self._value = self.steady_value
            else:
                self._value = mid

        # Add noise
        self._value += random.gauss(0, self.noise)
        return round(self._value, 3)


# ── Global generator state ──
generators: dict[str, SignalGenerator] = {}
update_interval: float = 1.0


async def handle_root(request: web.Request) -> web.Response:
    """Return flat JSON with all 19 signal values."""
    data: dict[str, Any] = {
        "timestamp": datetime.now(VN_TZ).isoformat(),
    }
    for gen in generators.values():
        val = gen.update(update_interval)
        data[gen.signal_id] = val
    return web.json_response(data)


async def handle_health(request: web.Request) -> web.Response:
    return web.json_response({"status": "healthy", "signals": len(generators)})


def create_app() -> web.Application:
    app = web.Application()
    app.router.add_get("/", handle_root)
    app.router.add_get("/api/health", handle_health)
    return app


def main():
    parser = argparse.ArgumentParser(description="WTP Plant Simulator HTTP Server")
    parser.add_argument("--port", type=int, default=9998, help="Listen port")
    parser.add_argument("--interval", type=float, default=1.0, help="Update interval (seconds)")
    args = parser.parse_args()

    global generators, update_interval
    update_interval = args.interval

    # Initialize generators
    for sig_cfg in SIGNALS:
        generators[sig_cfg["signal_id"]] = SignalGenerator(sig_cfg)

    print(f"WTP Simulator: {len(generators)} signals, port={args.port}, interval={args.interval}s")
    print(f"Signals: {', '.join(generators.keys())}")

    app = create_app()
    web.run_app(app, host="0.0.0.0", port=args.port, print=lambda *a: None)


if __name__ == "__main__":
    main()
