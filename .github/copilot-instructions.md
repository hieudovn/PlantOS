# PlantOS AI Coding Assistant Instructions

You are working on PlantOS, an Industrial Operational Platform.

Before planning or implementing any non-trivial change, read:

- `README.md`
- `docs/00-product-vision.md`
- `docs/01-project-constitution.md`
- `docs/10-high-level-architecture.md`
- `docs/20-data-model.md`
- `docs/80-working-rules.md`

## Core rules

- Do not bypass UNS/CDM.
- Do not bind UI directly to raw PLC tags.
- Do not let UI query TDengine, PostgreSQL, MQTT or Kafka directly.
- Do not create duplicate concepts for plant, area, asset, device, signal, measurement, event or alarm.
- Keep Edge and Center responsibilities separate.
- Prefer open-source infrastructure for commodity capabilities.
- Build PlantOS-specific value in data model, governance, visualization binding, UX, integration and productization.
- Use asset/signal/event APIs as boundaries.
- Every major architecture decision should create or update an ADR.
- Update documentation when changing architecture or data model.

## Expected working style

For each task, produce:

1. brief understanding of the task,
2. affected modules/files,
3. implementation plan,
4. code/document changes,
5. validation steps,
6. documentation updates if needed.

## Red flags

Stop and ask for architecture review if a task requires:

- direct database access from UI,
- new raw tag naming convention,
- changing UNS path structure,
- changing CDM core entities,
- adding free-form scripting/low-code behavior,
- adding write-back/control commands,
- replacing selected core infrastructure,
- introducing license-sensitive dependencies.
