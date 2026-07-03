# PlantOS Project Status — 2026-07-03

## Phase Completion Summary

| Phase | Status | Key Deliverables |
|-------|--------|-----------------|
| 0: Foundation | ✅ CLOSED | Vision, constitution, architecture, data model |
| 1: MVP Data Backbone | ✅ CLOSED | FastAPI, PostgreSQL, TDengine, Asset/Signal APIs |
| 2: Edge Runtime MVP | ✅ CLOSED | Edge Agent, DuckDB, MQTT, Store-and-Forward |
| 3: Visualization MVP | ✅ CLOSED | Product Shell, Trend, Diagram, GIS, Asset Tree |
| 4: Rule/Alarm Engine | ✅ CLOSED | Threshold alarms, Calculated Signals, Notifications |
| 5: MES/VF Integration | ✅ CLOSED | OPC UA Collector, VF Compressor, CDM Events, VPS Deploy |
| 6: Industrial Hardening | 🔄 2/8 done | JWT Auth, Edge Sync Fix ✅ — 6 tasks remaining |
| 7: Model Importer | ✅ CLOSED | Contract v2, Validate→Preview→Apply, JSON Schema |
| 8A: WTP Reference | ✅ COMPLETED | 92 signals, 47 assets, 8 scenarios, VF Simulator |
| 8B: Security Hardening | ✅ COMPLETED | New credentials, 5-step rotation, 0 old keys in code |
| 8B: Edge WTP OPC UA | 📋 Prompt ready | Multi-endpoint collector, auto-bind from contract |

---

## What Was Accomplished (Today — 2026-07-03)

### Security Hardening (Phase 8B)
- ✅ Rotated all credentials: API keys, DB passwords, JWT secret, MQTT auth
- ✅ Removed hardcoded `plantos-edge-key-2026` from all 54+ locations
- ✅ Fixed metadata sync auth bug (was silently failing)
- ✅ EMQX anonymous access disabled
- ✅ Frontend uses build-time env var (`VITE_API_KEY`) instead of hardcoded key
- ✅ Old key rejected (401), new keys working
- ✅ Full pipeline tested: Edge→Center→TDengine→Frontend all green

### UAT Fixes (Phase 8A)
- ✅ Logout button always visible in MVP mode
- ✅ Historian time range presets (10p/30p/1h/6h/12h) working
- ✅ Historian displays WTP SIMULATED quality data
- ✅ Timestamp display shows correct Vietnam time
- ✅ Diagram page supports WTP Process Flow
- ✅ Workspace dropdown shows all 3 plants
- ✅ Frontend API key fallback for MVP demo mode

---

## Current Deployment State (VPS)

| Component | Status | Endpoint |
|-----------|--------|----------|
| PlantOS Backend | ✅ Running | `:8000` |
| PostgreSQL | ✅ Running | `:5432` |
| TDengine | ✅ Running | `:6041` |
| EMQX (MQTT) | ✅ Running (auth required) | `:1883` |
| Edge Agent | ✅ Online | heartbeat OK |
| VF Compressor Sim | ✅ Running | OPC UA `:4840` |
| VF WTP Simulator | ✅ Running | OPC UA `:4841`, Scenario API `:8100` |
| Frontend (Nginx) | ✅ Running | `:80` |

### Data Pipelines
| Pipeline | Signals | Status |
|----------|---------|--------|
| VF Compressor → OPC UA 4840 → Edge → MQTT → Center → TDengine | 26 | ✅ |
| WTP → HTTP Ingest → Center → TDengine | 92 | ✅ |
| WTP → OPC UA 4841 → Edge | 92 | 📋 Planned (prompt ready) |

---

## Remaining Work (Prioritized)

### Priority 1 — Edge Consistency (1 task)
| # | Task | Status |
|---|------|--------|
| 8B-01 | Edge Agent WTP OPC UA Integration (118 signals unified) | 📋 Prompt ready |

### Priority 2 — Phase 6 Industrial Hardening (6 tasks)
| # | Task | Status |
|---|------|--------|
| 6-02 | Systemd Services (auto-start Edge Agent + VF) | ⬜ |
| 6-03 | Database Backup (daily cron) | ⬜ |
| 6-04 | Fix Heartbeat Auth | ⬜ |
| 6-05 | JWT Token Refresh (sliding expiration) | ⬜ |
| 6-06 | Fix Timestamp to Real UTC | ⬜ |
| 6-07 | Dead Letter Queue for Sync | ⬜ |

### Priority 3 — Code Quality (from Audit)
| # | Task |
|---|------|
| C1 | ErrorBoundary component |
| C2 | Remove 41 `: any` types |
| C3 | Replace hardcoded plant IDs with API-driven approach |
| C4 | Add rate limiting |
| C5 | Fix WebSocket reconnect backoff |

### Priority 4 — Documentation
| # | Task |
|---|------|
| D1 | Update `docs/90-roadmap.md` (stops at Phase 5) |
| D2 | Create Phase 6-8 closure docs |

---

## Next Step Recommendation

**1. Complete Edge WTP OPC UA (8B-01)** — 1 prompt, quick win. Unifies data pipeline, Edge Fleet shows 118 signals.

**2. Run Phase 6 tasks 6-02 through 6-07** — These are pre-written prompts, mostly mechanical. Systemd services + DB backup are critical for production readiness.

**3. Then move to Phase 8 Core Stabilization** — Address audit findings (ErrorBoundary, types, hardcoded IDs).
