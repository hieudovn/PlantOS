# PlantOS Edge

Edge runtime for PlantOS. Contains:

- `simulator/` — synthetic telemetry generator for MVP development
- `agent/` — future edge agent for on-site deployment
- `collectors/` — protocol collector prototypes (OPC UA, Modbus, MQTT)

Edge modules must be able to run independently from the Center for local buffering and simulation tests.

## Running the Simulator

```bash
# 1. Seed demo plant data (backend must be running)
cd ..
python scripts/seed_demo_plant.py --api-url http://localhost:8000

# 2. Start simulator
cd edge/simulator
pip install -r requirements.txt
python simulator.py --config ../../examples/demo-plant/demo-plant.yaml

# 3. Try different scenarios
python simulator.py --scenario pump_high_pressure --duration 30
python simulator.py --scenario breaker_trip --duration 30

# 4. Query ingested data
curl "http://localhost:8000/api/v1/measurements/current?asset_id=PUMP-101"
```
