# PlantOS AI Coding Assistant Instructions

You are working on PlantOS, an Industrial Operational Platform.

Before planning or implementing any non-trivial change, read:

- `README.md`
- `docs/00-product-vision.md`
- `docs/01-project-constitution.md`
- `docs/10-high-level-architecture.md`
- `docs/20-data-model.md`
- `docs/80-working-rules.md`
- `docs/81-ai-workflow.md`

When you need VPS access, SSH credentials, service URLs, or login info for any service (Center, Edge v1, Edge v2, Simulator, TDengine, Docker), read `local/dev-credentials.md` first.

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
- 🚫 NEVER change the running frontend Docker image without explicit PO permission. Only fix env vars/network on running container.

## Expected working style

PlantOS uses a multi-session AI workflow (see `docs/81-ai-workflow.md`):

- **V4 Pro (this session):** PM-Designer-Planner + Reviewer-Critic. Design tasks, write Coder prompts, review output. Only code directly for trivial scaffolding or minor review fixes.
- **V4 Flash (separate session):** Coder-Executioner + Tester. Read prompt from `docs/prompts/`, implement, test, report.

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
