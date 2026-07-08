# EV2-STAB — Edge v2 Stabilization & End-to-End Verification

> **Approved by:** SA + PM
> **Status:** Ready for Coder
> **Rule:** NO feature expansion. NO E2V2-7. NO S7. Fix & verify only.

---

## Context

Edge v2 đã qua 8/9 phase (CF-0 đến E2V2-6) nhưng runtime stability ~35-45%. Cần dừng feature, fix P0/P1, chạy E2E smoke trước internal demo.

## Plan Reference

- SA Review: `PlantOS_Edge_v2_SA_Current_State_Stabilization_Review.md`
- PM Response: `docs/phase-edge-v2-productization-plan.md` (EV2-STAB section)
- ADR: `docs/adr/ADR-edge-v2-sync-path-mvp.md` (Sync Path Option A)
- Constitution: `docs/01-project-constitution.md`

## Sync Path Decision (READ FIRST)

```
APPROVED: Option A — Legacy measurements table as MVP sync source

Connector → RawReading → ProcessingEngine → processed value
  → ghi vào measurements (legacy table)
  → StoreAndForward v1 đọc measurements
  → sync về Center

raw_measurements = diagnostic only
processed_measurements = reserved for future StoreAndForwardV2
measurements = active sync source
```

## Giai đoạn 1 — Fix P0

### STAB-01: Fix Connector Central Polling Architecture

**Problem:** OPC UA connector dùng `yield` trong `_poll_loop()` → async generator chạy trong `asyncio.create_task()` gây TypeError. Tất cả connector cần follow cùng pattern: `start()` chỉ establish connection, `read_tags()` là primary data path.

**Required changes (ALL connectors):**
- OPC UA: bỏ `yield` trong `_poll_loop()`, `start()` chỉ connect, `read_tags()` poll + return
- Modbus TCP: verify `read_tags()` hoạt động, không dùng `yield`
- MQTT Subscribe: verify callback cache pattern hợp lệ, `read_tags()` trả về từ cache
- HTTP Poll: verify `read_tags()` thực hiện HTTP GET và parse
- Modbus RTU: verify `read_tags()` pattern giống Modbus TCP

**Acceptance:**
```
- Tất cả connector start() không raise TypeError
- read_tags() trả về list[RawReading] hoặc []
- Connection status chính xác
- Reconnect không block agent
```

**Test:**
```bash
PYTHONPATH=$(pwd) python -c "
from edge_v2.agent.connectors.base import BaseConnector
# Verify all 5 connectors implement read_tags()
# Verify start() returns without error
print('STAB-01 PASS' if ok else 'STAB-01 FAIL')
"
```

---

### STAB-02: Fix Dockerfile Build Context

**Problem:** Dockerfile chỉ COPY `agent/` và `console/` — thiếu `edge/agent/*.py` (buffer, sync, health, publisher) mà Edge v2 import.

**Fix:** Docker build context là repo root, Dockerfile copy thêm edge/agent reused libs:

```dockerfile
# Copy Edge v1 reused libraries
COPY edge/agent/buffer.py /app/edge/agent/buffer.py
COPY edge/agent/sync.py /app/edge/agent/sync.py
COPY edge/agent/health.py /app/edge/agent/health.py
COPY edge/agent/publisher.py /app/edge/agent/publisher.py
COPY edge/__init__.py /app/edge/__init__.py
COPY edge/agent/__init__.py /app/edge/agent/__init__.py
```

Hoặc: thay đổi build context để include toàn bộ repo, điều chỉnh COPY path.

**Acceptance:**
```bash
cd edge-v2
docker compose -f docker-compose.edge-v2.yml build
docker compose -f docker-compose.edge-v2.yml up -d
curl http://localhost:8011/api/status
# → 200 OK JSON
```

---

### STAB-03: Fix install.sh Repo/Branch

**Problem:** `install.sh` hardcode git clone URL và branch có thể sai.

**Fix:**
- Dùng `https://github.com/hieudovn/PlantOS.git` làm repo URL
- Dùng `main` làm branch (vì Edge v2 commits đang trên main)
- Hoặc: bỏ git clone fallback, chỉ support local install từ source có sẵn
- Ghi chú trong INSTALL.md về repo URL/branch

**Acceptance:**
```bash
grep -E "hieudovn/PlantOS|github.com.*plantos" edge-v2/install.sh
# → URL đúng
grep "branch" edge-v2/install.sh
# → main hoặc feature/edge-v2 đúng
```

---

### STAB-04: Verify Processing Loop Signature

**Problem:** `main.py` processing_loop gọi `ProcessingEngine.apply()` với `history=` keyword — có thể không khớp signature thực tế.

**Fix:** Đọc `engine.py` signature, đảm bảo main.py gọi đúng:
```python
result = self.processing.apply(
    raw_value=reading.raw_value,
    profile=profile,
    signal_id=reading.signal_id,
    timestamp=reading.timestamp,
)
```

Và `write_raw`:
```python
self.processing.write_raw(
    signal_id=reading.signal_id,
    raw_value=reading.raw_value,
    source_ref=reading.source_ref,
    connector=conn_id,
    quality_hint=reading.quality_hint or "GOOD",
    timestamp=reading.timestamp,
)
```

**Acceptance:**
```
- Processing loop chạy không TypeError
- RawReading → raw_measurements
- Processed value → measurements (legacy table, để sync)
- Không crash trong 5 phút
```

---

## Giai đoạn 2 — Fix P1 + E2E Smoke

### STAB-05: Auth Fail Fast for Missing Crypto

**Problem:** Auth fallback sang SHA-256/HMAC nếu thiếu bcrypt/itsdangerous — không an toàn cho production.

**Fix:** Trong `LocalAuthManager.__init__()`:
```python
if not _bcrypt_available():
    raise RuntimeError("bcrypt required for production. Install: pip install bcrypt")
if not _itsdangerous_available():
    raise RuntimeError("itsdangerous required for production. Install: pip install itsdangerous")
```

Thêm `EDGE_DEV_INSECURE_AUTH=true` env var để cho phép fallback trong test/dev.

**Acceptance:**
```
- Thiếu bcrypt → crash lúc startup với message rõ
- Thiếu itsdangerous → crash lúc startup với message rõ
- EDGE_DEV_INSECURE_AUTH=true → cho phép fallback
- pip install bcrypt itsdangerous → chạy bình thường
```

---

### STAB-06: Canonical Config Path

**Problem:** Draft/active/backup config keys có thể conflict (`connector_x` vs `connectors.x`).

**Fix:** Chuẩn hóa single source of truth:
```yaml
# Active config path
connectors.<connector_id>

# Draft path
_drafts.connectors.<connector_id>

# Backup path
_backups.connectors.<connector_id>.<timestamp>
```

Sửa `ConfigManager` để:
- `get_draft()` → `self._data["_drafts"]["connectors"][connector_id]`
- `apply_draft()` → copy từ `_drafts.connectors.<id>` → `connectors.<id>` + backup cũ vào `_backups`

**Acceptance:**
```
- Active connector config luôn ở connectors.<id>
- Draft không bị nhầm với active
- Backup có timestamp rõ ràng
- Rollback restore đúng config trước đó
```

---

### STAB-07: ADR Sync Path (ĐÃ XONG)

✅ File: `docs/adr/ADR-edge-v2-sync-path-mvp.md`

Không cần code change. Chỉ cần Coder đọc và tuân thủ.

---

### STAB-08: Data E2E Smoke

**Mục tiêu:** Chứng minh luồng dữ liệu hoàn chỉnh từ simulator đến Center.

**Kịch bản:**
1. Start HTTP simulator trên port 9999:
   ```bash
   python edge-v2/simulator/protocol_servers/http_test_server.py --port 9999
   ```
   Output: `{"pump101_flow": 12.5, "tank101_level": 85.3}`

2. Start Edge v2 agent

3. Setup: login, first-run admin password

4. Tạo HTTP Poll connector:
   ```json
   {
     "connector_id": "http_test_01",
     "type": "http_poll",
     "enabled": true,
     "connection": {"url": "http://localhost:9999/api/test/measurements"},
     "tags": [
       {"source_ref": "pump101_flow", "signal_id": "EDGEV2-PUMP-101.flow_rate", "data_type": "float"}
     ],
     "poll_interval_seconds": 5
   }
   ```

5. Validate → Test → Apply → Confirm

6. Tạo processing profile:
   ```json
   {"profile_id": "scale_test", "steps": [{"type": "scale_offset", "params": {"scale": 0.1}}]}
   ```

7. Assign profile to signal

8. Đợi 10s, kiểm tra:
   ```bash
   curl -H "Cookie: ..." http://localhost:8011/api/measurements/latest
   # → có EDGEV2-PUMP-101.flow_rate với processed value
   ```

9. Kiểm tra Center:
   ```bash
   curl http://localhost:8000/api/v1/edge-nodes
   # → EDGEV2-PC-01 online
   ```

**Acceptance:**
```
- Simulator → Edge → processing → buffer → Center sync pass
- Processed value trong local API
- Center thấy Edge online
- Backlog về 0 sau sync
```

---

### STAB-09: Command E2E Smoke

**Mục tiêu:** Chứng minh pull-based command hoạt động end-to-end.

**Kịch bản:**
1. Center login → lấy JWT
2. Tạo sync_now command:
   ```bash
   curl -X POST http://localhost:8000/api/v1/edge-nodes/EDGEV2-PC-01/commands \
     -H "Authorization: Bearer $TOKEN" \
     -d '{"command_type":"sync_now"}'
   ```
3. Đợi 35s (Edge polls every 30s + 5s safety)
4. Kiểm tra command status:
   ```bash
   curl http://localhost:8000/api/v1/edge-nodes/EDGEV2-PC-01/commands
   # → status: "success"
   ```
5. Tương tự test `reload_config`
6. Tương tự test `restart_connector` (cần có connector đang chạy)

**Acceptance:**
```
- sync_now: pending → executing → success
- reload_config: pending → executing → success
- restart_connector: pending → executing → success
- Command history hiển thị trong Center API
- restart_agent: fail gracefully nếu không có supervisor
```

---

### STAB-10: Docker Smoke Test

**Mục tiêu:** Chứng minh Docker packaging hoạt động.

**Kịch bản:**
```bash
cd edge-v2
docker compose -f docker-compose.edge-v2.yml down -v 2>/dev/null || true
docker compose -f docker-compose.edge-v2.yml up -d --build
sleep 10
curl http://localhost:8011/api/status
curl http://localhost:8011/api/version
docker compose -f docker-compose.edge-v2.yml logs --tail 20
```

**Acceptance:**
```
- docker compose build không lỗi
- docker compose up -d → container running
- /api/status → 200 OK JSON
- /api/version → version info
- docker logs không có exception loop
```

---

## Giai đoạn 3 — Hardening + Report

### STAB-11: Smoke Script

Tạo `edge-v2/scripts/smoke_e2e.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail
PASS=0; FAIL=0

check() {
    local name="$1"; shift
    if "$@"; then echo "✅ $name"; PASS=$((PASS+1))
    else echo "❌ $name"; FAIL=$((FAIL+1)); fi
}

# 1. Boot
check "Boot" curl -sf http://localhost:8011/api/status > /dev/null

# 2. Auth
check "Login" curl -sf -X POST http://localhost:8011/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"test123"}' > /dev/null

# 3-8. ... (data E2E, command E2E steps)

echo "---"
echo "Results: $PASS passed, $FAIL failed"
[ $FAIL -eq 0 ] && echo "SMOKE PASS" || echo "SMOKE FAIL"
exit $FAIL
```

**Acceptance:** `bash smoke_e2e.sh` → exit 0.

---

### STAB-12: Verification Report

Tạo `docs/reports/edge-v2-stab-verification-report.md` với bảng:

| Gate | Result | Evidence | Notes |
|---|---|---|---|
| Boot smoke | PASS/FAIL | command output | |
| Auth smoke | PASS/FAIL | curl/browser result | |
| Data E2E | PASS/FAIL | API/DB/UI evidence | |
| Command E2E | PASS/FAIL | command history | |
| Docker smoke | PASS/FAIL | docker logs/curl | |
| Known P0 | 0 required | list | |
| Known P1 | 0 required | list | |
| **Internal demo** | **GO/NO-GO** | PM + SA decision | |

---

### STAB-13: Go/No-Go Decision

PM reviews verification report, recommends GO/NO-GO. SA reviews trước internal demo.

---

## Report Format (After Each STAB Task)

```
Task: STAB-XX
Changed files:
  - path/to/file1
  - path/to/file2
What was fixed:
  - brief description
Test command:
  exact command
Test output:
  exact output
Pass/fail: PASS / FAIL
Known issues:
  - any remaining issues
Next recommended action:
  - next STAB task or STOP
```

## Commit Rules

```
- Small focused commits only
- Message format: fix(edge-v2): STAB-XX description
- No feature additions
- No refactor beyond scope of fix
- Push after each STAB task (not batched)
```

## Red Flags

```
STOP if:
- Fix requires modifying Edge v1 (unless critical compatibility)
- Fix requires breaking Center API change
- Fix introduces new feature or protocol
- Fix scope expands beyond STAB task
- E2E smoke reveals regression in previously working feature
```
