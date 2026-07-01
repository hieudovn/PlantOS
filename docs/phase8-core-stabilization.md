# PlantOS Phase 8 — Core Foundation Stabilization

> **Status:** 🔜 NEXT | **SA Directive:** 2026-07-01  
> **Phase 7 Final Closure:** `docs/status-phase7-closure-model-importer.md`

## 1. Phase 8 Objective

Củng cố nền tảng trước khi mở rộng tính năng. Phase 8 tập trung vào **stability, test quality, và golden path validation** — không thêm feature mới phức tạp.

## 2. SA Mandate

```
✅ Core foundation stabilization
✅ Golden path validation (end-to-end)
✅ Historian hardening
✅ Integration test quality gates
❌ NO Phase E Manifest Generation
❌ NO new complex features
❌ NO UI redesign
```

## 3. Task Breakdown

### 8-01: Golden Path Integration Test

**Goal:** Một test script chạy end-to-end toàn bộ pipeline hiện tại.

```
VF Simulator → OPC UA → Edge Agent → DuckDB → Sync → TDengine → API → UI
```

- [ ] CREATE `tests/integration/test_golden_path.py`
- [ ] Test: Start with clean state → seed VF-DEMO → verify assets/signals in API
- [ ] Test: Edge Agent sync → verify measurements in TDengine via API
- [ ] Test: Historian query → verify data returned for known signal
- [ ] Test: System metrics → verify CPU/RAM/disk reported
- [ ] Test: Contract validate → preview → apply cycle

### 8-02: Historian Hardening

**Goal:** Đảm bảo Historian query ổn định dưới các điều kiện biên.

- [ ] FIX: Handle empty time range gracefully (no crash, no timeout)
- [ ] FIX: Handle non-existent signal_id (return empty, not error)
- [ ] ADD: Query timeout (default 30s, configurable)
- [ ] ADD: Response size limit (max 100K points per query)
- [ ] TEST: Concurrent queries (10 simultaneous history requests)
- [ ] TEST: Large time range query (7 days of 1s data)

### 8-03: Edge Agent Health Check Hardening

**Goal:** Tăng resilience của Edge Agent.

- [ ] ADD: Edge health check endpoint responds within 2s even under load
- [ ] ADD: DuckDB WAL auto-cleanup on startup (prevent lock issues)
- [ ] FIX: Graceful shutdown (SIGTERM → flush buffer → close)
- [ ] ADD: `/api/health` on Edge (simple liveness check)
- [ ] MONITOR: Log backlog growth rate (warn if > 1000/minute)

### 8-04: Backup Verification

**Goal:** Đảm bảo backup thực sự restore được.

- [ ] CREATE `scripts/backup/verify-pg-backup.sh` — dry-run restore test
- [ ] CREATE `scripts/backup/verify-td-backup.sh` — taosdump verify
- [ ] ADD: Weekly verify cron job (Sunday 3AM)
- [ ] TEST: Manual restore of latest backup to temp DB

### 8-05: VF Systemd Fix

**Goal:** Virtual Factory auto-start ổn định.

- [ ] DEBUG: Tại sao `plantos-vf.service` luôn "activating"?
- [ ] FIX: Đảm bảo VF khởi động OPC UA server trước khi Edge connect
- [ ] ADD: `After=plantos-vf.service` trong `plantos-edge.service`
- [ ] VERIFY: `sudo systemctl restart plantos-vf` → active trong 10s

### 8-06: Quality Gates

**Goal:** Thiết lập quality bar trước khi merge code.

- [ ] CREATE `.github/workflows/quality-gate.yml` (hoặc script local)
- [ ] CHECK: All backend tests pass (`pytest backend/tests/`)
- [ ] CHECK: Frontend builds without errors (`npm run build`)
- [ ] CHECK: Docker Compose starts without errors
- [ ] CHECK: No hardcoded secrets in code (`grep -r "password\|secret\|key" --include="*.py"`)
- [ ] CHECK: API responds within 2s for basic queries

## 4. Implementation Order

```
8-05 VF Systemd Fix    (30min) ← Quick win, unblocks stability
8-01 Golden Path Test  (2h)    ← Foundation for all other tests
8-02 Historian Hardening (1.5h)← Data integrity
8-03 Edge Health Check  (1h)    ← Resilience
8-04 Backup Verification (1h)   ← Disaster recovery
8-06 Quality Gates      (1h)    ← CI/CD foundation
```

## 5. Phase 8 Acceptance Criteria

- [ ] Golden path test passes end-to-end
- [ ] Historian handles edge cases without crashing
- [ ] Edge Agent survives restart cycles
- [ ] Backup can be verified and restored
- [ ] VF starts reliably via systemd
- [ ] Quality gate script catches common issues
- [ ] All existing APIs and UI unchanged
- [ ] No new features added (per SA directive)

## 6. What Phase 8 Does NOT Include

- ❌ Phase E Manifest Generation
- ❌ New UI features
- ❌ New API endpoints (beyond health/metrics hardening)
- ❌ Database schema changes
- ❌ New AI/ML capabilities
- ❌ Multi-tenant support
- ❌ Production deployment (stays on single VPS)
