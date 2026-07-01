#!/bin/bash
# Kill old VF
pkill -f virtual_factory.main 2>/dev/null
sleep 2

# Start new VF with compressor config
export PYTHONPATH=/opt/virtual-factory/src:$PYTHONPATH
cd /opt/virtual-factory
nohup python3 -m virtual_factory.main run \
  --config /opt/virtual-factory/configs/plants/compressor_train_benchmark_01.yaml \
  --steps 0 \
  --dt 1.0 \
  --opcua-endpoint opc.tcp://0.0.0.0:4840 \
  > /tmp/vf.log 2>&1 &
echo "VF started PID=$!"
sleep 6
echo "=== VF Output ==="
head -5 /tmp/vf.log
echo "..."
tail -5 /tmp/vf.log
