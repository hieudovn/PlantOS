# ADR: Edge v2 MVP Sync Path — Legacy Measurements Table

> **ADR ID:** ADR-edge-v2-sync-path-mvp  
> **Date:** 2026-07-08  
> **Status:** ACCEPTED  
> **Deciders:** SA + PM  

---

## Context

Edge v2 ProcessingEngine tạo hai bảng DuckDB:
- `raw_measurements` — diagnostic only, không sync
- `processed_measurements` — dành cho StoreAndForwardV2 tương lai

Edge v1 `StoreAndForward` hiện đọc từ bảng `measurements`. Cần chốt sync path cho MVP.

## Decision

**Option A — Dùng legacy `measurements` table làm sync source cho MVP.**

```
Connector → RawReading → ProcessingEngine → processed value
  → ghi vào `measurements` (legacy table)
  → StoreAndForward v1 đọc `measurements`
  → sync về Center
```

Trong đó:
- `raw_measurements` = local diagnostic, retention 3 ngày
- `processed_measurements` = reserved cho StoreAndForwardV2 tương lai
- `measurements` = active sync source cho MVP

## Rationale

- Tận dụng `StoreAndForward` v1 đã ổn định
- Giảm scope EV2-STAB
- Đủ cho internal demo
- Không cần viết `StoreAndForwardV2` mới

## Consequences

- Processed value được ghi vào cả `measurements` (để sync) và `processed_measurements` (để dự phòng)
- `raw_measurements` chỉ dùng local debug
- Sau internal demo sẽ chuyển sang `StoreAndForwardV2` với `processed_measurements`
- Backlog count = `COUNT(*) FROM measurements WHERE synced = FALSE`

## Alternatives Considered

**Option B — StoreAndForwardV2 với processed_measurements:** Từ chối vì tăng scope EV2-STAB, cần code mới, chưa cần cho internal demo.
