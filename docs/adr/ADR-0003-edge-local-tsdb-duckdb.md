# ADR-0003: Edge Local Time-Series Database — DuckDB

## Status

Accepted

## Date

2026-06-30

## Context

PlantOS Edge nodes cần local time-series storage để:

1. **Buffer dữ liệu** khi mất kết nối Center (store-and-forward)
2. **Lưu trữ ngắn hạn** — retention 1-2 tháng, tự xóa dữ liệu cũ nhất khi đầy
3. **Phân tích tại Edge** — chạy truy vấn analytical, feature engineering cho ML
4. **Anomaly detection** — phát hiện bất thường ngay tại Edge, không phụ thuộc Center
5. **Siêu nhẹ** — chạy được trên edge node hạn chế tài nguyên (Raspberry Pi, industrial PC, container nhỏ)

Center đã chọn TDengine (ADR-0001) cho historian chính. Tuy nhiên TDengine là database server — quá nặng và không phù hợp cho embedded edge use case. Cần một lựa chọn embedded, analytical-capable cho Edge.

## Decision

Sử dụng **DuckDB** làm Edge local TSDB engine.

```text
Center:  TDengine (server)    → historian chính, scale lớn
Edge:    DuckDB  (embedded)   → local buffer, analytics, anomaly detection
```

### Vai trò DuckDB trên Edge

- Nhận write từ Edge Collector (protocol adapters → normalized measurements)
- Lưu measurement với schema mirror Center (ts, signal_id, value, quality, source)
- Phục vụ local analytical query (trend, aggregate, window function)
- Hỗ trợ Python UDF cho ML/anomaly detection model
- Store-and-forward: batch query → HTTP POST đến Center khi kết nối
- Retention: `DELETE FROM measurements WHERE ts < NOW() - INTERVAL '60 DAYS'` qua scheduled job

### Schema (Edge)

```sql
CREATE TABLE measurements (
    ts          TIMESTAMPTZ NOT NULL,
    signal_id   VARCHAR NOT NULL,
    value       DOUBLE,
    quality     VARCHAR,
    source      VARCHAR,
);
CREATE INDEX idx_measurements_signal_ts ON measurements(signal_id, ts);
```

### Deployment

```text
pip install duckdb
# → 1 file: edge_data.duckdb
# → không server process, không config
```

## Alternatives Considered

### Option A: TimescaleDB

Pros:

- Hypertable, compression, retention policy built-in
- Full PostgreSQL ecosystem
- Multi-writer, production-proven

Cons:

- Yêu cầu PostgreSQL server (~100MB+ RAM baseline)
- Overkill cho edge: vacuum, WAL, connection pool, authentication
- Không có analytical engine vectorized như DuckDB
- ML/anomaly detection phải làm ở application layer

**Rejected** — quá nặng cho edge node hạn chế tài nguyên.

### Option B: SQLite

Pros:

- Nhẹ nhất (~1MB)
- Zero config
- Python stdlib

Cons:

- Row-based storage — không tối ưu cho analytical query
- Không có window function mạnh (phiên bản cũ)
- Không hỗ trợ Python UDF trong DB
- Mọi ML/anomaly phải kéo data ra pandas — chậm, tốn RAM

**Rejected** — không đáp ứng yêu cầu analytics + anomaly detection tại Edge.

### Option C: TDengine (embedded)

Pros:

- Cùng stack với Center
- Đồng bộ schema tự nhiên
- Time-series native, compression tốt

Cons:

- Vẫn là server process — không nhẹ bằng DuckDB embedded
- Không có Python UDF trong DB
- Overkill cho edge buffer 1-2 tháng

**Rejected** — DuckDB nhẹ hơn, analytical mạnh hơn cho edge use case.

### Option D: DuckDB

Pros:

- **Embedded** — 1 file, import `duckdb` là chạy, không server, không config
- **Analytical engine** — columnar, vectorized, window function, `ASOF JOIN`
- **Python UDF** — chạy model anomaly score trực tiếp trong SQL
- **Nén tốt** — columnar compression ~5-10x so với row-based
- **SQL dialect** — tương thích PostgreSQL, cùng syntax với Center
- **Đọc trực tiếp CSV/Parquet** — không cần ETL
- **Single binary / pip install** — triển khai cực nhanh

Cons:

- Single-writer (đủ cho edge 1 node)
- Không có built-in retention policy (cần cron job SQL đơn giản)
- Không phải time-series database chuyên dụng (không hypertable, không automatic partitioning)

**Accepted** — trade-off chấp nhận được. Single-writer không ảnh hưởng vì edge node chỉ có 1 collector writer. Retention cron job là 1 dòng SQL. DuckDB mạnh nhất ở phân tích + ML tại Edge — đúng thứ PlantOS Edge cần.

## Consequences

### Positive

- Edge deployment cực nhẹ: `pip install duckdb` + 1 file
- ML/anomaly detection chạy trực tiếp trong SQL — không cần ETL ra pandas
- Cùng SQL dialect PostgreSQL với Center → context switch thấp
- Backup/restore đơn giản: copy 1 file
- Có thể query trực tiếp CSV/Parquet từ collector

### Trade-offs

- Schema Edge ≠ Schema Center (DuckDB table ≠ TDengine supertable) — nhưng cả hai đều dùng measurement canonical model, sync qua API, không vấn đề
- Retention phải quản lý thủ công (DELETE SQL cron) thay vì built-in policy
- Cần thêm `duckdb` vào Edge dependencies (~30MB)

### Constraints

- DuckDB chỉ dùng trên Edge — không thay thế TDengine trên Center
- DuckDB không expose API trực tiếp — mọi truy vấn qua Edge Agent
- Schema Edge mirror measurement canonical model từ `docs/20-data-model.md`

## Impacted Areas

- `edge/simulator/` — thêm DuckDB writer cho local buffer
- `edge/agent/` — DuckDB query + store-and-forward logic
- `docs/15-storage-and-historian-design.md` — cập nhật Edge storage section
- `docs/60-edge-center-strategy.md` — cập nhật local historian capability
- `deployment/docker-compose.yml` — không cần service mới (embedded)

## Review Date

Sau Phase 1 MVP — benchmark ingestion throughput và query latency trên target edge hardware.

## Notes

DuckDB có thể nâng cấp lên MotherDuck (managed DuckDB) nếu sau này cần edge sync multi-node — nhưng không nằm trong MVP scope.
