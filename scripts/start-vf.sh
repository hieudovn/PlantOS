#!/bin/bash
export PYTHONPATH=/opt/virtual-factory/src:$PYTHONPATH
cd /opt/virtual-factory
nohup python3 -m virtual_factory.main run \
  --config /opt/virtual-factory/configs/plants/compressor_train_benchmark_01.yaml \
  --steps 0 \
  --dt 1.0 \
  --opcua-endpoint opc.tcp://0.0.0.0:4840 \
  > /tmp/vf.log 2>&1 &
echo "VF PID: $!"
sleep 5
echo "=== VF LOG ==="
head -20 /tmp/vf.log
echo "=== PORT 4840 ==="
ss -tlnp | grep 4840 || echo "Port 4840 not listening"
