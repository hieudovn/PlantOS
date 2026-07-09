#!/usr/bin/env python3
"""HTTP Signal Simulator — 19 WTP signals for Edge v2 mirror connector.

Runs on port 9998 (replacing 3-signal version).
Returns JSON with 19 WTP signals that match signal_ids in both DEMO-PLANT and EDGEV2-DEMO.
"""
import json, math, random, time
from http.server import HTTPServer, BaseHTTPRequestHandler

PORT = 9998
t0 = time.time()

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        t = time.time() - t0
        data = {
            "PUMP-101.flow_rate": round(100 + 20 * math.sin(t * 0.1) + random.uniform(-1, 1), 2),
            "PUMP-101.discharge_pressure": round(7 + 2 * math.sin(t * 0.12) + random.uniform(-0.2, 0.2), 2),
            "PUMP-101.running_status": 1.0,
            "PUMP-101.vibration_rms": round(2.5 + 0.5 * math.sin(t * 0.15) + random.uniform(-0.1, 0.1), 2),
            "MOTOR-101.motor_current": round(50 + 10 * math.sin(t * 0.08) + random.uniform(-0.5, 0.5), 2),
            "MOTOR-101.motor_temperature": round(65 + 5 * math.sin(t * 0.05) + random.uniform(-0.3, 0.3), 1),
            "MOTOR-101.running_status": 1.0,
            "TANK-101.tank_level": round(3.5 + 1.5 * math.sin(t * 0.03) + random.uniform(-0.1, 0.1), 2),
            "TANK-101.temperature": round(22 + 3 * math.sin(t * 0.04) + random.uniform(-0.2, 0.2), 1),
            "RAW-WATER-QUALITY-STATION-101.raw_turbidity": round(15 + 10 * math.sin(t * 0.02) + random.uniform(-1, 1), 1),
            "RAW-WATER-QUALITY-STATION-101.raw_ph": round(7.2 + 0.5 * math.sin(t * 0.01) + random.uniform(-0.05, 0.05), 2),
            "RAW-WATER-QUALITY-STATION-101.raw_temperature": round(20 + 5 * math.sin(t * 0.015) + random.uniform(-0.2, 0.2), 1),
            "FILTER-101.filter_dp": round(0.5 + 0.3 * math.sin(t * 0.06) + random.uniform(-0.05, 0.05), 2),
            "FILTER-101.effluent_flow": round(95 + 10 * math.sin(t * 0.07) + random.uniform(-1, 1), 2),
            "CLEAR-WATER-TANK-101.level": round(4.0 + 1.0 * math.sin(t * 0.025) + random.uniform(-0.1, 0.1), 2),
            "HSP-101.flow_rate": round(200 + 30 * math.sin(t * 0.09) + random.uniform(-2, 2), 2),
            "HSP-101-MOTOR.motor_current": round(80 + 15 * math.sin(t * 0.085) + random.uniform(-0.5, 0.5), 2),
            "COAG-PUMP-101.flow_rate": round(5 + 2 * math.sin(t * 0.11) + random.uniform(-0.1, 0.1), 2),
            "CHLORINE-PUMP-101.flow_rate": round(3 + 1 * math.sin(t * 0.13) + random.uniform(-0.05, 0.05), 2),
        }
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def log_message(self, format, *args):
        pass

if __name__ == "__main__":
    print(f"HTTP Simulator (19 signals) on port {PORT}")
    HTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
