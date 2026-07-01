# Phase 6 — Task 6-06: Fix Timestamp to Real UTC

> **Designer:** V4 Pro | **Date:** 2026-07-01 | **Priority:** P1

## Context

**Đây là bug nghiêm trọng nhất còn tồn tại.** TDengine đang lưu timestamp **local time (UTC+7) nhưng label UTC**. Hậu quả:

- Historian query bị lệch 7 giờ nếu dùng UTC conversion
- Workaround hiện tại: TrendChart query bằng local time (bỏ `toUTC()`) — chỉ đúng khi user ở UTC+7
- Khi deploy multi-plant multi-timezone → **dữ liệu sai hoàn toàn**

## Root Cause Chain

```
VF Simulator                    Edge Agent                   TDengine
───────────                    ──────────                   ────────
sinh timestamp                  write buffer                store
bằng local time                dùng timestamp               as UTC
(UTC+7)                        từ simulator                 (label "Z")
     │                              │                          │
     ▼                              ▼                          ▼
 13:00 ICT ──────────────►  "2026-07-01T13:00:00" ──────► 13:00Z
 (06:00 UTC)                                                (sai: lẽ ra 06:00Z)
```

Timestamp bị sai ở **cả 2 nguồn**:
1. VF simulator sinh timestamp = `datetime.now()` → local time
2. Edge Agent dùng timestamp từ simulator mà không convert sang UTC

## Fix Strategy

**Sửa ở Edge Agent** — nơi duy nhất chịu trách nhiệm chuẩn hóa data trước khi sync:

```
Simulator raw → Edge Agent → Convert to UTC → DuckDB → Sync → TDengine (UTC)
```

VF simulator giữ nguyên (không sửa vì là external component).

## Implementation Checklist

- [ ] READ `edge/agent/main.py` — SignalGenerator.write và OpcUaCollector._poll_loop
- [ ] MODIFY `edge/agent/main.py` — SignalGenerator: dùng `datetime.now(timezone.utc)` (đã có nhưng cần verify)
- [ ] MODIFY `edge/agent/collectors/opcua/collector.py` — `_poll_loop`: đảm bảo timestamp là UTC
- [ ] MODIFY `frontend/src/features/historian/TrendChart.tsx` — khôi phục `toUTC()` conversion
- [ ] VERIFY: query TDengine — timestamp có dạng `HH:MM:SSZ` khớp với UTC thật
- [ ] VERIFY: Historian UI hiển thị đúng dữ liệu với `toUTC()` conversion
- [ ] UPDATE `docs/15-storage-and-historian-design.md` — ghi chú timestamp convention

## Detailed Instructions

### 1. Verify/ Fix SignalGenerator (main.py)

File: `edge/agent/main.py`

Dòng hiện tại (~line 122):
```python
now = datetime.now(timezone.utc)  # ← ĐÃ ĐÚNG
```

Nếu đã là `timezone.utc` → **không cần sửa**. Coder verify.

### 2. Fix OpcUaCollector (collector.py)

File: `edge/agent/collectors/opcua/collector.py`

Dòng hiện tại trong `_poll_loop` (~line 57):
```python
now = datetime.now(timezone.utc)  # ← CẦN VERIFY
```

Nếu đã là `timezone.utc` → không cần sửa. Nếu là `datetime.now()` (không timezone) → sửa thành:
```python
from datetime import datetime, timezone
now = datetime.now(timezone.utc)
```

### 3. Fix DuckDB Buffer write

File: `edge/agent/buffer.py`

Verify rằng `write()` method không tự ý convert timestamp. Timestamp từ collector đã là UTC, buffer chỉ lưu trữ.

### 4. Restore toUTC() in TrendChart

File: `frontend/src/features/historian/TrendChart.tsx`

KHÔI PHỤC `toUTC()` conversion đã bị xóa trong Phase 6-01:

```typescript
// Convert local YYYY-MM-DDTHH:mm to UTC ISO for API query
const toUTC = (ts: string): string => {
    if (!ts || ts.length < 16) return ts;
    const d = new Date(ts);
    return isNaN(d.getTime()) ? ts : d.toISOString().slice(0, 19) + "Z";
};
const utcFrom = toUTC(localFrom);
const utcTo = toUTC(localTo);

// Use utcFrom/utcTo in API call:
queryFn: () => getHistory({ signal_id: sid, from: utcFrom, to: utcTo }),
```

### 5. Deploy & Verify

```bash
# Sau khi sửa Edge Agent files:
# 1. Kill Edge Agent
# 2. Xóa DuckDB cũ (để tránh data timestamp hỗn hợp):
rm edge_data.duckdb
# 3. Khởi động lại Edge Agent
# 4. Build & deploy frontend

# Verify: query TDengine trực tiếp
docker exec plantos-tdengine taos -s \
  "SELECT ts, value FROM d_COMP01_CORE_speed ORDER BY ts DESC LIMIT 3;"

# Expected: timestamp gần với UTC hiện tại (không phải local time)
# Ví dụ: 2026-07-01 07:30:00.000 (UTC) thay vì 2026-07-01 14:30:00.000 (ICT)
```

### 6. Validation

| Check | Expected |
|---|---|
| `date -u` on VPS | `Wed Jul  1 07:30:00 UTC 2026` |
| Latest TDengine timestamp | ~07:30:00Z (khớp UTC, không phải 14:30:00) |
| Historian UI query | Chọn 14:00 local → API query `to=07:00Z` → có data |
| `toUTC()` conversion | `2026-07-01T14:00` local → `2026-07-01T07:00:00Z` |

## ⚠️ IMPORTANT WARNING

**Phải xóa DuckDB cũ** (`edge_data.duckdb`) khi deploy fix này. Data cũ có timestamp sai (local time labeled UTC) — nếu trộn với data mới (UTC thật), Historian query sẽ hiển thị sai.

Sau khi xóa DuckDB:
- Edge Agent sẽ tạo DuckDB mới
- OPC UA collector sẽ poll và ghi data với timestamp UTC
- Sync sẽ flush data mới vào TDengine
- TDengine data cũ vẫn tồn tại (không xóa) — nhưng data mới sẽ đúng

## Notes

- Không sửa VF simulator — nó là external component
- Không cần migrate TDengine data cũ (chấp nhận data cũ sai timestamp)
- Đây là **breaking change** về mặt dữ liệu — cần thông báo trong release notes
