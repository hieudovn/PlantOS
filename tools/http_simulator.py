#!/usr/bin/env python3
"""HTTP Signal Simulator — returns WTP signals for Edge v2 mirror connector.
Runs on port 9999. Returns JSON with 3 signals: flow_rate, discharge_pressure, motor_current.
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
            "MOTOR-101.motor_current": round(50 + 10 * math.sin(t * 0.08) + random.uniform(-0.5, 0.5), 2),
        }
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def log_message(self, format, *args):
        pass  # silent

if __name__ == "__main__":
    print(f"HTTP Simulator on port {PORT}")
    HTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
