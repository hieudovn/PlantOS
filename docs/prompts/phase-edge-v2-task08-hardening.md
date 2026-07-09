# E2V2-8: Production Readiness Hardening

> **SA Gate:** ✅ CONDITIONALLY APPROVED 2026-07-09
> **Parent Report:** `docs/reports/edge-v2-e2v2-7-pm-sa-review.md`
> **Constraint:** Edge v1 remains PRIMARY. No production switch until all 6 requirements met.

## Context

SA reviewed E2V2-7 PM audit (56 issues: 5 P0, 15 P1, 26 P2). Approved E2V2-8 hardening phase with 6 mandatory requirements before any production switch can be considered.

---

## SA Requirements (6 Mandatory Gates)

### Gate 1: Resolve All P0 Issues

- [ ] **1.1** Remove hardcoded password from `tools/vps_execute_e2v2_7b.py:11`
  - Replace `PlantOS@2026!` with `os.environ.get("PLANTOS_CENTER_PASSWORD", "")`
  - Exit with error if not set when needed, not silently continue

- [ ] **1.2** Remove hardcoded credentials from `tools/compare_v1_v2_data.py:39`
  - Replace `"admin"` / `"PlantOS@2026!"` with env vars
  - `PLANTOS_CENTER_USERNAME` / `PLANTOS_CENTER_PASSWORD`

- [ ] **1.3** Remove hardcoded password from `scripts/seed_edgev2_test.py:30`
  - Same env var pattern as above

- [ ] **1.4** Fix default `session_secret` in `edge-v2/agent/config/config.edge-v2.yaml:8`
  - Change from `plantos-edge-default-secret` to require override
  - Agent must refuse to start if session_secret equals the default
  - Add env var `EDGE_SESSION_SECRET` support

- [ ] **1.5** Add safety gate to `tools/vps_execute_e2v2_7b.py` Phase 3
  - Require `--i-know-this-is-production` flag before executing `docker stop`
  - Or check `PLANTOS_ENV=dev` before allowing destructive operations

### Gate 2: Center Auth + v2 Data Flow

- [ ] **2.1** Fix heartbeat 401 — v2 must authenticate with Center
  - Heartbeat currently returns 401 Unauthorized
  - Verify Center API key or JWT auth works for edge nodes

- [ ] **2.2** Prove v2 data reaches Center
  - After heartbeat fix, verify backlog clears (current backlog: 21+)
  - Confirm measurements appear in Center for EDGEV2-DEMO workspace

- [ ] **2.3** Verify sync path (ADR Option A — legacy measurements table)
  - Confirm `StoreAndForward.flush()` successfully writes to Center
  - Check for duplicate data, timestamp accuracy

### Gate 3: Meaningful Side-by-Side Comparison

- [ ] **3.1** Run `compare_v1_v2_data.py` with v2 data in Center
  - Requires Gate 2 completion (v2 data must be in Center first)
  - Minimum 1 hour comparison
  - All shared signals within ±5% tolerance

- [ ] **3.2** Fix `--hours 0.5` int truncation bug
  - `compare_v1_v2_data.py` argparse `type=int` → change to `type=float`
  - Update runbook references

- [ ] **3.3** Document comparison results in `edge-v2-migration-prep.md`

### Gate 4: Minimum Tests for Migration Tools

- [ ] **4.1** Add smoke test for `tools/migrate_v1_config_to_v2.py`
  - Test with sample v1 config → verify output connectors
  - Test with missing fields → verify graceful degradation
  - File: `edge-v2/tests/test_migrate_config.py`

- [ ] **4.2** Add smoke test for `tools/compare_v1_v2_data.py`
  - Mock Center API responses → verify comparison logic
  - Test tolerance boundary cases
  - File: `edge-v2/tests/test_compare_data.py`

- [ ] **4.3** Add smoke test for `scripts/seed_edgev2_test.py`
  - Mock HTTP responses → verify plant/asset/signal creation
  - Test idempotency (409 Conflict handling)
  - File: `edge-v2/tests/test_seed.py`

### Gate 5: Docker Hardening

- [ ] **5.1** Add non-root user to Dockerfile
  ```dockerfile
  RUN useradd -m -s /bin/bash plantos
  USER plantos
  ```
  - Ensure data volume permissions work with non-root user

- [ ] **5.2** Create `edge-v2/.dockerignore`
  ```
  __pycache__/
  *.pyc
  .git/
  .env
  *.log
  data/
  tests/
  ```

- [ ] **5.3** Fix apt cache cleanup
  - `RUN apt-get ... && rm -rf /var/lib/apt/lists/*` must be on same RUN line

- [ ] **5.4** Add `ENV PYTHONPATH=/app` to Dockerfile
  - Make imports deterministic regardless of CWD

### Gate 6: Production Switch Readiness Report

- [ ] **6.1** Create `docs/reports/edge-v2-production-readiness.md`
  - All 5 gates above verified with evidence
  - Rollback runbook tested (Phase 5 already passed)
  - Migration runbook reviewed
  - Risk register updated
  - Final GO/NO-GO recommendation

---

## Files to Create

```
edge-v2/.dockerignore
edge-v2/tests/
  __init__.py
  test_migrate_config.py
  test_compare_data.py
  test_seed.py
docs/reports/
  edge-v2-production-readiness.md
```

## Files to Modify

```
tools/vps_execute_e2v2_7b.py        — remove hardcoded password, add safety gate
tools/compare_v1_v2_data.py         — remove hardcoded creds, fix --hours type
scripts/seed_edgev2_test.py         — remove hardcoded password
edge-v2/agent/config/config.edge-v2.yaml  — session_secret hardening
edge-v2/agent/auth/auth.py          — refuse default session_secret
edge-v2/Dockerfile                  — non-root user, apt cleanup, PYTHONPATH
edge-v2/agent/main.py               — fix heartbeat auth (if needed)
```

---

## SA Constraints

```text
1. DO NOT claim production readiness until all 6 gates pass.
2. DO NOT disable, stop, or deprecate Edge v1.
3. Edge v1 remains PRIMARY throughout.
4. Production switch requires separate SA gate review after E2V2-8.
```

## Red Flags

- STOP if: any change affects Edge v1
- STOP if: hardcoded credentials remain in ANY committed file
- STOP if: session_secret default is not rejected at startup
- STOP if: destructive script runs without safety gate
