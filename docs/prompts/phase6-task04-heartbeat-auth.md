# Phase 6 — Task 6-04: Fix Edge Heartbeat Auth

> **Designer:** V4 Pro | **Date:** 2026-07-01 | **Priority:** P0 (small fix)

## Context

Edge Agent gửi heartbeat đến `/api/v1/edge-nodes/heartbeat` mỗi 10 giây nhưng luôn nhận **401 Unauthorized**. Nguyên nhân: HealthReporter không gửi `X-API-Key` header.

```
[httpx] POST /api/v1/edge-nodes/heartbeat "HTTP/1.1 401 Unauthorized"  ← MỖI 10 GIÂY
```

## Root Cause

`edge/agent/main.py` tạo HealthReporter với URL nhưng **không truyền `api_key`**:

```python
# main.py line ~80
self.health = HealthReporter(
    self.cfg["heartbeat"]["url"], self.node_id, self.cfg["heartbeat"]["interval_seconds"]
    # ← THIẾU api_key
)
```

Trong khi `sync.py` đã có `api_key` và gửi đúng header.

## Implementation Checklist

- [ ] READ `edge/agent/health.py` — understand HealthReporter constructor
- [ ] MODIFY `edge/agent/health.py` — add `api_key` parameter, send `X-API-Key` header
- [ ] MODIFY `edge/agent/main.py` — pass `api_key` to HealthReporter
- [ ] SCP updated files to VPS
- [ ] RESTART Edge Agent (via systemd after P0-01 done, or manual)
- [ ] VERIFY: `tail -f /tmp/edge.log | grep heartbeat` shows 200 OK instead of 401

## Detailed Instructions

### 1. Read health.py

Đọc file `edge/agent/health.py` để hiểu constructor và HTTP call hiện tại. Coder cần xác định:

- Constructor nhận tham số gì
- HTTP request gửi thế nào (httpx, requests, aiohttp?)
- Có chỗ nào để thêm header không

### 2. Modify health.py

Thêm `api_key` parameter và gửi header:

```python
# Pattern (pseudo-code — adapt to actual implementation):
class HealthReporter:
    def __init__(self, url: str, node_id: str, interval: int, api_key: str = ""):
        self.url = url
        self.node_id = node_id
        self.interval = interval
        self.api_key = api_key
        # ... existing init ...
    
    async def _send_heartbeat(self):
        headers = {}
        if self.api_key:
            headers["X-API-Key"] = self.api_key
        
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(self.url, json={
                "node_id": self.node_id,
                "status": "online",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }, headers=headers)
            # ... existing response handling ...
```

### 3. Modify main.py

Truyền `api_key` vào HealthReporter:

```python
# In EdgeAgent.__init__:
self.health = HealthReporter(
    self.cfg["heartbeat"]["url"],
    self.node_id,
    self.cfg["heartbeat"]["interval_seconds"],
    api_key=self.cfg.get("api_key", ""),  # ← THÊM DÒNG NÀY
)
```

### 4. Deploy & Verify

```bash
# SCP updated files to VPS
scp edge/agent/health.py plantos@103.97.132.249:/opt/plantos/edge/agent/
scp edge/agent/main.py plantos@103.97.132.249:/opt/plantos/edge/agent/

# Restart Edge (manual for now, systemd after P0-01)
ssh plantos@103.97.132.249
sudo pkill -f "main.py"
cd /opt/plantos/edge/agent && nohup python3 -u main.py > /tmp/edge.log 2>&1 &

# Wait 15s then check
tail -f /tmp/edge.log | grep heartbeat
# Expected: "POST /api/v1/edge-nodes/heartbeat HTTP/1.1 200 OK"
```

### 5. Validation

| Check | Expected |
|---|---|
| `grep heartbeat /tmp/edge.log \| tail -5` | All show `200 OK` (không còn 401) |
| `curl -s http://localhost:8001/api/status` | Edge still running, sync backlog 0 |
| Backend health | `curl localhost:8000/health` → healthy |

## Notes

- File `health.py` có thể dùng `requests` (sync) hoặc `httpx` (async) — cần đọc code thực tế để adapt
- Nếu `health.py` dùng sync HTTP, cần đảm bảo chạy trong thread pool để không block event loop
- API key đã có trong `config.yaml`: `api_key: {EDGE_API_KEY}`
