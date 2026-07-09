#!/usr/bin/env python3
"""Wrapper: run comparison tool with password from file."""
import subprocess, sys, os

# Write password to file (avoids shell escaping issues)
PW = "PlantOS@2026!"
PW_FILE = "/tmp/plantos_center_pw.txt"
with open(PW_FILE, "w") as f:
    f.write(PW)

# Run comparison directly via Python (not shell subprocess)
os.environ["PLANTOS_CENTER_PASSWORD"] = PW
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tools.compare_v1_v2_data import main
sys.argv = [
    "compare_v1_v2_data.py",
    "--hours", "1",
    "--center-url", "http://localhost:8000",
    "--signal-ids", "PUMP-101.flow_rate", "PUMP-101.discharge_pressure", "MOTOR-101.motor_current",
]
main()
