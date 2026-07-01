#!/usr/bin/env python3
"""Start VF with compressor train config + OPC UA."""
import sys
sys.argv = [
    "virtual-factory", "run",
    "--config", "/opt/virtual-factory/configs/plants/compressor_train_benchmark_01.yaml",
    "--steps", "0",
    "--dt", "1.0",
    "--opcua-endpoint", "opc.tcp://0.0.0.0:4840",
]
from virtual_factory.main import main
main()
