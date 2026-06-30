# PlantOS Edge

Edge runtime for PlantOS. Contains:

- `simulator/` — synthetic telemetry generator for MVP development
- `agent/` — future edge agent for on-site deployment
- `collectors/` — protocol collector prototypes (OPC UA, Modbus, MQTT)

Edge modules must be able to run independently from the Center for local buffering and simulation tests.
