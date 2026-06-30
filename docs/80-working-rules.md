# PlantOS Working Rules

## 1. Purpose

This document defines how humans and AI assistants should work on PlantOS.

It is designed to prevent uncontrolled growth, duplicated concepts, inconsistent modules, broken architecture and AI-generated drift.

## 2. Required reading before any major task

Before planning or implementing a major feature, read:

1. `README.md`
2. `docs/00-product-vision.md`
3. `docs/01-project-constitution.md`
4. `docs/10-high-level-architecture.md`
5. `docs/20-data-model.md`
6. Relevant module document.

No feature should be planned without checking the constitution and data model.

## 3. Role model

### Product Owner

Owns product direction, priorities, scope and use cases.

### Solution Architect

Owns architecture, module boundaries, integration strategy and technical coherence.

### Data Architect

Owns UNS, CDM, schema, data quality and semantic context.

### UX/Product Designer

Owns design system, product shell, user journeys and visualization consistency.

### Backend Developer

Implements APIs, services, registries, historian, rules and integrations.

### Frontend Developer

Implements product shell, visualization runtime, UI components and workspace UX.

### DevOps/Platform Engineer

Owns deployment, Docker, Kubernetes, edge runtime, CI/CD and observability.

### AI Assistant / Codex

Can draft documents, propose architecture, write code, generate tests and refactor.

AI cannot approve its own output.

## 4. AI working rules

Any AI assistant working on PlantOS must:

- read the constitution first,
- preserve UNS/CDM principles,
- avoid direct UI-to-database coupling,
- avoid hardcoded tags/assets,
- keep Edge and Center responsibilities separate,
- document assumptions,
- propose tests or validation steps,
- avoid creating new concepts when existing concepts can be reused,
- update documentation when architecture changes.

## 5. Prompt pattern for AI development

Use this pattern when assigning work to Codex or another AI coding assistant:

```text
You are working on PlantOS.

Before making changes, read:
- README.md
- docs/01-project-constitution.md
- docs/10-high-level-architecture.md
- docs/20-data-model.md
- any relevant module docs.

Task:
[describe task]

Constraints:
- Do not bypass UNS/CDM.
- Do not hardcode raw PLC tags in UI/rules.
- Do not let UI query storage directly.
- Maintain edge-center responsibility split.
- Prefer open-source infrastructure and PlantOS-specific governance/modeling.

Expected output:
- implementation plan,
- files to change,
- code changes,
- tests or validation steps,
- documentation updates if needed.
```

## 6. Documentation rules

Every major module must have:

- purpose,
- responsibilities,
- non-responsibilities,
- inputs,
- outputs,
- data model impact,
- API/event contract,
- security considerations,
- edge/center behavior if applicable.

## 7. Architecture decision records

Use ADRs for decisions that affect:

- database selection,
- message broker selection,
- frontend framework,
- edge manager strategy,
- historian design,
- UNS structure,
- CDM structure,
- external integration contracts,
- license-sensitive components.

Recommended path:

```text
docs/adr/ADR-0001-title.md
```

ADR template:

```text
# ADR-0001: Title

## Status
Proposed / Accepted / Rejected / Superseded

## Context

## Decision

## Alternatives considered

## Consequences

## Review date
```

## 8. Feature definition rule

Before implementation, each feature should define:

- user role,
- problem,
- target workflow,
- data objects,
- APIs/events,
- UI screens,
- permission model,
- edge/center impact,
- test criteria.

## 9. Low-code/rule design rules

Rules and flows must not become uncontrolled user scripts.

Every rule/flow must have:

- owner,
- version,
- scope,
- environment,
- input schema,
- output schema,
- test mode,
- approval status,
- rollback,
- audit log,
- resource limit.

## 10. Visualization rules

Visualization must:

- bind to asset/signal/alarm/event objects,
- avoid raw tag binding,
- use shared state colors and severity rules,
- support role-based access,
- use shared design tokens,
- record version and owner.

## 11. Data rules

Do not create duplicate definitions of:

- plant,
- area,
- asset,
- device,
- signal,
- measurement,
- event,
- alarm,
- production order,
- operation,
- material,
- work order.

If a new concept is needed, update the data model documentation.

## 12. Review checklist

Before merging or accepting work, check:

- Does it align with product vision?
- Does it violate the constitution?
- Does it duplicate an existing concept?
- Does it bypass UNS/CDM?
- Does it couple UI to storage?
- Does it work for both real and simulated data?
- Does it consider Edge and Center behavior?
- Does it need an ADR?
- Does it update documentation?

## 13. Definition of done

A task is done only when:

- code or document is complete,
- assumptions are explicit,
- tests/validation are described or implemented,
- affected docs are updated,
- no constitution rule is violated,
- next steps are clear.
