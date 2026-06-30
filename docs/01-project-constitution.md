# PlantOS Project Constitution

This constitution defines the non-negotiable rules for PlantOS design and development.

Any architecture, code, feature, document, AI-generated plan, or implementation task must follow this constitution unless an explicit architecture decision record approves an exception.

## 1. Mission

PlantOS exists to provide a governed operational foundation for industrial plants.

It connects edge data, time-series storage, Unified Namespace, Canonical Data Model, visualization, rules, alarms and integration services into one coherent platform.

## 2. Core values

PlantOS must be:

- **Industrial-first**: designed around plants, areas, assets, systems, devices, signals, events and alarms.
- **Open architecture**: built on open standards and open-source components where practical.
- **Vendor-neutral**: able to integrate with existing PLC, SCADA, Historian, MES, CMMS/EAM, ERP and analytics systems.
- **UNS-native**: all operational data must be addressable through a governed namespace.
- **CDM-native**: business/application objects must follow a canonical data model.
- **Composable**: modules must be replaceable without breaking the entire platform.
- **Edge-resilient**: edge nodes must continue critical local buffering and visualization when center connectivity is lost.
- **Governed low-code**: low-code flows and rules must be constrained, versioned, tested and auditable.
- **AI-ready**: AI must consume contextualized data and APIs, not raw PLC tags.
- **Security by design**: identity, authorization, audit and network boundaries are first-class concerns.

## 3. Non-goals

PlantOS must not become:

- a PLC programming tool,
- a DCS or SCADA replacement,
- a pure Historian product,
- a dashboard-only product,
- a free-form Node-RED clone,
- a ThingsBoard clone,
- a MES,
- an ERP,
- a CMMS/EAM,
- an uncontrolled plugin marketplace.

PlantOS can integrate with these systems or provide selected capabilities, but it must remain the governed operational platform layer.

## 4. Architecture laws

### Law 1: No raw-data coupling

Applications must not directly depend on raw PLC tag names, protocol-specific identifiers, or historian table names.

### Law 2: No UI-to-database shortcut

UI widgets must not read directly from TDengine, PostgreSQL, Kafka, MQTT or any storage backend.

All UI access must go through approved APIs or the Visualization Data Adapter.

### Law 3: UNS is the operational address space

Operational data must be published and consumed through governed UNS paths.

Ad-hoc topic creation is not allowed outside namespace policy.

### Law 4: CDM is the application contract

MES, Virtual Factory, analytics, AI and external applications must use CDM-aligned objects and APIs instead of private duplicated models.

### Law 5: Asset context is mandatory

Signals and events must be linked to asset, device, area, system or process context wherever possible.

### Law 6: Edge and center responsibilities must be separated

Edge handles local collection, buffering, normalization, local rules and lightweight visualization.

Center handles governance, global registry, advanced rules, cross-site visualization, integration and analytics services.

### Law 7: Low-code must be governed

Any rule or flow must have:

- owner,
- version,
- scope,
- environment,
- approval status,
- test result,
- rollback path,
- audit log,
- resource limit.

### Law 8: Replaceability is required

Core infrastructure components such as TSDB, message broker, dashboard engine or map engine must be abstracted behind service interfaces where practical.

### Law 9: Documentation is part of the product

Every major module must have design documentation before implementation grows beyond prototype level.

### Law 10: AI output is not accepted without review

AI-generated code, architecture and documentation must be reviewed against this constitution, the data model, and the roadmap before being accepted.

## 5. Decision rules

When choosing between alternatives, prefer the option that:

1. preserves UNS/CDM consistency,
2. reduces hard coupling,
3. supports edge-center separation,
4. improves product governance,
5. increases long-term maintainability,
6. avoids reimplementing mature open-source infrastructure,
7. protects PlantOS product identity and architecture.

## 6. Required review checklist

Before accepting any major change, verify:

- Does it bypass UNS or CDM?
- Does it hardcode asset or tag names?
- Does it introduce UI-to-storage coupling?
- Does it create a hidden shadow system?
- Does it break edge-center responsibility separation?
- Does it duplicate functionality better handled by an open-source component?
- Does it need documentation or an architecture decision record?
- Does it affect MES, Virtual Factory or AI integration contracts?

If any answer is unclear, the change must be reviewed by the architecture role before implementation.
