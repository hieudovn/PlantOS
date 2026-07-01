# Phase 6 — Task 6-07: Dead Letter Queue for Sync Pipeline

> **Designer:** V4 Pro | **Date:** 2026-07-01 | **Priority:** P1

## Context

Sync pipeline hiện tại **block hoàn toàn** khi oldest rows bị reject (ví dụ: signal không tồn tại trong PostgreSQL). Đã xảy ra trong Phase 6-01: 87K rows demo signal kẹt `synced=FALSE`, sync không thể tiến lên rows mới.

## Current Behavior (vấn đề)

```
DuckDB: [old_reject_1, old_reject_2, ..., good_1, good_2]
                │
                ▼
sync.flush(100) → get_unsynced → [old_reject_1..100]
                │
                ▼
Backend: signal không tồn tại → accepted=0
                │
                ▼
mark_synced(0) → KHÔNG mark → rows vẫn unsynced
                │
                ▼
Loop lại → get_unsynced → [old_reject_1..100] ← VÔ HẠN
```

## Target Behavior (dead letter queue)

```
DuckDB: [old_reject_1, old_reject_2, ..., good_1, good_2]
                │
                ▼
sync.flush(100) → get_unsynced → [old_reject_1..100]
                │
                ▼
Backend: signal không tồn tại → accepted=0, rejected=100
                │
                ▼
Nếu rejected > 0 và retry_count >= 3:
  mark_synced(100) ← SKIP rows không sync được
  log WARNING: "Dead letter: 100 rows skipped after 3 retries"
                │
                ▼
Lần flush sau → get_unsynced → [good_1, good_2, ...]
                │
                ▼
Backend: signal tồn tại → accepted=2 ✅
```

## Design Decision

- **Retry count:** 3 lần, sau đó skip (không retry vô hạn)
- **Lưu retry state:** trong DuckDB (thêm column `retry_count INTEGER DEFAULT 0`)
- **Không tạo bảng dead letter riêng** — quá phức tạp cho MVP. Chỉ skip + log.
- **Không thay đổi backend** — chỉ sửa Edge Agent

## Implementation Checklist

- [ ] MODIFY `edge/agent/buffer.py` — thêm `retry_count` column, update `mark_synced`
- [ ] MODIFY `edge/agent/buffer.py` — thêm `increment_retry_count()` method
- [ ] MODIFY `edge/agent/sync.py` — logic retry/skip khi `accepted=0`
- [ ] VERIFY: simulate rejected signals → sau 3 lần → rows được skip
- [ ] VERIFY: rows mới vẫn sync bình thường sau khi skip old rows
- [ ] UPDATE `docs/15-storage-and-historian-design.md` — document dead letter behavior

## Detailed Instructions

### 1. buffer.py — Add retry_count

File: `edge/agent/buffer.py`

Thêm column vào schema:

```python
def _init_schema(self):
    self.conn.execute("""
        CREATE TABLE IF NOT EXISTS measurements (
            ts          TIMESTAMPTZ NOT NULL,
            signal_id   VARCHAR NOT NULL,
            value       DOUBLE,
            quality     VARCHAR,
            source      VARCHAR,
            synced      BOOLEAN DEFAULT FALSE,
            retry_count INTEGER DEFAULT 0
        )
    """)
    # ... existing index ...
```

> **Migration:** Nếu DuckDB đã có data cũ (không có column `retry_count`), `CREATE TABLE IF NOT EXISTS` sẽ không thêm column. Coder cần thêm logic migration:
> ```python
> # Add column if not exists (DuckDB supports this)
> try:
>     self.conn.execute("ALTER TABLE measurements ADD COLUMN retry_count INTEGER DEFAULT 0")
> except Exception:
>     pass  # Column already exists
> ```

Thêm method `increment_retry_count`:

```python
def increment_retry_count(self, count: int):
    """Increment retry_count for oldest N unsynced rows."""
    self.conn.execute("""
        UPDATE measurements SET retry_count = retry_count + 1
        WHERE rowid IN (
            SELECT rowid FROM measurements WHERE synced = FALSE
            ORDER BY ts ASC LIMIT ?
        )
    """, [count])
```

Modify `get_unsynced` — thêm `retry_count` vào output (để sync.py quyết định skip):

```python
def get_unsynced(self, limit: int = 1000, max_retries: int = 3) -> list[dict]:
    """Get measurements not yet synced, up to max_retries."""
    rows = self.conn.execute("""
        SELECT ts, signal_id, value, quality, source, retry_count
        FROM measurements WHERE synced = FALSE AND retry_count < ?
        ORDER BY ts ASC LIMIT ?
    """, [max_retries, limit]).fetchall()
    return [
        {"timestamp": r[0].isoformat(), "signal_id": r[1], "value": r[2],
         "quality": r[3], "source": r[4], "retry_count": r[5]}
        for r in rows
    ]

def skip_dead_letters(self, max_retries: int = 3) -> int:
    """Mark rows with retry_count >= max_retries as synced (dead letter)."""
    self.conn.execute("""
        UPDATE measurements SET synced = TRUE
        WHERE synced = FALSE AND retry_count >= ?
    """, [max_retries])
    return self.conn.execute("SELECT changes()").fetchone()[0]  # DuckDB row count
```

### 2. sync.py — Retry/Skip Logic

File: `edge/agent/sync.py`

Modify `flush` method:

```python
MAX_RETRIES = 3

async def flush(self, batch_size: int = 100) -> int:
    """Flush unsynced data. Skip rows that fail after MAX_RETRIES."""
    
    # 1. First, skip dead letters (rows that already exceeded retries)
    skipped = self.buffer.skip_dead_letters(MAX_RETRIES)
    if skipped > 0:
        logger.warning(f"Dead letter: skipped {skipped} rows after {MAX_RETRIES} retries")
    
    # 2. Get fresh unsynced rows (excluding dead letters)
    unsynced = self.buffer.get_unsynced(batch_size, MAX_RETRIES)
    if not unsynced:
        return 0

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            headers = {"X-API-Key": self.api_key} if self.api_key else {}
            resp = await client.post(self.ingest_url, json={
                "source": self.edge_node_id,
                "measurements": unsynced,
            }, headers=headers)
            
            if resp.status_code in (200, 201):
                data = resp.json()
                synced = data.get("accepted", 0)
                rejected = len(unsynced) - synced
                
                if synced > 0:
                    self.buffer.mark_synced(synced)
                
                # Increment retry count for rejected rows
                if rejected > 0:
                    self.buffer.increment_retry_count(rejected)
                    logger.warning(
                        f"Flushed {synced}/{len(unsynced)} — "
                        f"{rejected} rejected (will retry up to {MAX_RETRIES}x)"
                    )
                else:
                    logger.info(f"Flushed {synced}/{len(unsynced)} measurements")
                
                return synced
            else:
                logger.warning(f"Flush failed: HTTP {resp.status_code}")
                return 0
    except Exception as e:
        logger.warning(f"Flush error: {e}")
        return 0
```

### 3. Deploy & Verify

```bash
# SCP updated files
scp edge/agent/buffer.py plantos@103.97.132.249:/opt/plantos/edge/agent/
scp edge/agent/sync.py plantos@103.97.132.249:/opt/plantos/edge/agent/

# Restart Edge Agent
# (via systemd: sudo systemctl restart plantos-edge)

# Monitor
tail -f /tmp/edge.log | grep -E "Flushed|Dead letter"
```

### 4. Validation

| Check | Expected |
|---|---|
| Sync với signals hợp lệ | `Flushed 10/10 measurements` |
| Sync với signals không tồn tại | `Flushed 0/10 — 10 rejected (will retry up to 3x)` |
| Sau 3 lần retry | `Dead letter: skipped 10 rows after 3 retries` |
| Rows mới vẫn sync sau khi skip | `Flushed 10/10 measurements` |
| Backlog không tăng vô hạn | `unsynced` count giảm dần |

### 5. Unit Test (optional but recommended)

Tạo script test nhỏ:

```python
# test_dead_letter.py
import duckdb
import os
import sys
sys.path.insert(0, '.')
from buffer import DuckDBBuffer
from sync import StoreAndForward

# Setup
if os.path.exists("test_dl.duckdb"):
    os.remove("test_dl.duckdb")
buffer = DuckDBBuffer("test_dl.duckdb")

# Write 5 test measurements
for i in range(5):
    buffer.write([{"timestamp": "2026-07-01T00:00:00Z", "signal_id": f"TEST.{i}",
                    "value": i, "quality": "GOOD", "source": "test"}])

# Simulate 3 rejections
for _ in range(3):
    buffer.increment_retry_count(5)

# Skip dead letters
skipped = buffer.skip_dead_letters(3)
print(f"Skipped: {skipped}")  # Expected: 5

# Verify no unsynced remain
assert buffer.count_unsynced() == 0, f"Expected 0, got {buffer.count_unsynced()}"
print("✅ Dead letter test passed")
```

## Notes

- Không thay đổi backend — `accepted`/`rejected` response giữ nguyên
- DuckDB column migration an toàn — không mất data
- `skip_dead_letters` dùng DuckDB `changes()` để đếm — cần verify function này có sẵn trong DuckDB version đang dùng
- Nếu `changes()` không hoạt động, fallback sang: count trước khi UPDATE, UPDATE, count sau
