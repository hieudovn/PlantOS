# Phase 1 — Tasks 1-3: Repository Structure, Docker Compose, FastAPI Skeleton

> **Status:** ✅ COMPLETED (2026-06-30)
> **Exception:** Designer tự thực hiện do đây là scaffolding thuần túy — không có business logic, không có risk về constitution violation.
> **Workflow rule:** Từ Task 4 trở đi, tuân theo `docs/81-ai-workflow.md` (Designer V4 Pro → Coder V4 Flash → Reviewer V4 Pro).

## Context

Khởi tạo skeleton cho PlantOS Phase 1: cấu trúc thư mục, Docker Compose infrastructure, và FastAPI backend với `/health` endpoint. Không implement business logic.

## Plan Reference

- `docs/11-repository-structure.md`
- `docs/13-backend-service-design.md`
- `docs/14-api-contract-mvp.md`
- `docs/19-deployment-design.md`
- `docs/adr/ADR-0001-mvp-technology-decisions.md`

## Implementation Checklist

- [x] 34 directories created (backend, frontend, edge, deployment, examples, packages)
- [x] `deployment/docker-compose.yml` — 6 services (postgres, tdengine, emqx, backend, frontend, edge-simulator)
- [x] `deployment/env.example` — 16 environment variables
- [x] `backend/pyproject.toml` — FastAPI + SQLAlchemy + Alembic + pytest
- [x] `backend/app/main.py` — FastAPI app + `/health`
- [x] `backend/app/core/config.py` — Pydantic Settings
- [x] `backend/tests/test_health.py` — health endpoint test
- [x] `backend/Dockerfile` — multi-stage Python 3.11
- [x] Module placeholders (7 modules, empty `__init__.py`)
- [x] Frontend, Edge, Packages placeholders

## Test Results

```
tests/test_health.py::test_health_check PASSED [100%]
1 passed in 0.47s
```

## Issues Resolved

| Issue | Resolution |
|---|---|
| Python 3.12 not available locally | Adjusted `requires-python` to `>=3.11`, Dockerfile to `python:3.11-slim` |
| Hatchling unable to detect package | Added `[tool.hatch.build.targets.wheel] packages = ["app"]` |

## Constitution Compliance

- [x] No UNS/CDM bypass
- [x] No UI-to-DB coupling
- [x] No raw tag binding
- [x] Edge/Center separation maintained
- [x] No duplicate concepts
- [x] All directories follow approved structure
