"""HTTP Test Server — returns JSON measurement data for HTTP Poll connector testing.

Endpoints:
    GET /api/test/measurements — returns test sensor values
    GET /api/health — health check

Usage:
    python -m edge_v2.simulator.protocol_servers.http_test_server [--port 8080]
"""

import argparse
import json
import logging
from datetime import datetime, timezone

from aiohttp import web

logger = logging.getLogger(__name__)


async def handle_measurements(request: web.Request) -> web.Response:
    """Return test measurement data."""
    data = {
        "pump101_flow": 12.5,
        "pump101_pressure": 7.2,
        "tank101_level": 85.3,
        "motor101_status": 1,
        "quality_turbidity": 15.8,
        "energy_power": 245.0,
        "temperature": 42.5,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    return web.json_response(data)


async def handle_health(request: web.Request) -> web.Response:
    return web.json_response({"status": "healthy"})


def create_app() -> web.Application:
    app = web.Application()
    app.router.add_get("/api/test/measurements", handle_measurements)
    app.router.add_get("/api/health", handle_health)
    return app


def run_server(port: int = 8080):
    logger.info("Starting HTTP test server on port %d", port)
    app = create_app()
    web.run_app(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="HTTP Test Server")
    parser.add_argument("--port", type=int, default=8080, help="Port to listen on")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    run_server(args.port)
