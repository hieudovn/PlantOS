# Phase 3 — Task 3-01: Edge Local Web UI + Device Monitoring

> **Designer:** DeepSeek V4 Pro | **Date:** 2026-06-30

## Context

Edge Agent hiện tại chạy headless (terminal only). Cần web UI nhẹ để:
- Giám sát trạng thái (DuckDB stats, sync backlog, MQTT)
- Xem dữ liệu real-time (latest measurements per device/signal)
- Thiết lập cơ bản (xem config, connection status)
- Chạy trên cùng event loop với agent, không cần process riêng

## Architecture

```
Edge Agent (Python, port 8001)
├── Collector → DuckDB → MQTT → Sync (đã có)
└── aiohttp HTTP Server (thêm mới):
    ├── GET  /api/status              ← DuckDB stats, MQTT, sync backlog, uptime
    ├── GET  /api/measurements/latest ← latest values per signal (current snapshot)
    ├── GET  /api/measurements/recent ← 50 most recent measurements
    ├── GET  /api/config              ← current config (read-only, sanitized)
    └── GET  /                       ← HTML dashboard (auto-refresh 5s)

Center Frontend
└── Edge Fleet → click node → detail panel fetch từ Edge API
```

## Đã Có Sẵn (Từ Phase 1-2)

| Chức năng | Implementation |
|---|---|
| Backup/sync khi mất kết nối | `edge/agent/sync.py` — store-and-forward, tự flush khi kết nối |
| Lưu trữ ngắn hạn | `edge/agent/buffer.py` — DuckDB, 60-day retention, auto-cleanup |
| MQTT publish | `edge/agent/publisher.py` — paho-mqtt → EMQX |
| HTTP ingest fallback | `edge/agent/sync.py` — POST /api/v1/measurements/ingest |

## Implementation Checklist

- [ ] CREATE `edge/agent/web.py` — aiohttp HTTP server + all routes
- [ ] CREATE `edge/agent/templates/dashboard.html` — inline HTML dashboard
- [ ] MODIFY `edge/agent/main.py` — integrate web server vào event loop
- [ ] MODIFY `edge/agent/requirements.txt` — +aiohttp, +aiohttp-jinja2
- [ ] MODIFY `frontend/src/features/edge-fleet/EdgeFleetPage.tsx` — click row → detail

## Detailed Instructions

### 1. `edge/agent/requirements.txt` — Add

```
aiohttp>=3.9.0
```

### 2. `edge/agent/web.py` — HTTP Server

```python
"""Edge Agent HTTP server — status, monitoring, basic admin."""

import json
import time
from pathlib import Path
from aiohttp import web

start_time = time.time()

# References set by main.py after init
_buffer = None
_publisher = None
_sync_manager = None
_config = None


def setup(buffer, publisher, sync_mgr, config):
    global _buffer, _publisher, _sync_manager, _config
    _buffer = buffer
    _publisher = publisher
    _sync_manager = sync_mgr
    _config = config


async def handle_status(request):
    """JSON status endpoint."""
    conn = _buffer.conn
    total = conn.execute("SELECT COUNT(*) FROM measurements").fetchone()[0]
    unsynced = _buffer.count_unsynced()
    db_size = Path(_buffer.path).stat().st_size / (1024 * 1024) if Path(_buffer.path).exists() else 0

    return web.json_response({
        "node_id": _config["edge_node_id"],
        "uptime_seconds": int(time.time() - start_time),
        "duckdb": {
            "total_rows": total,
            "unsynced": unsynced,
            "synced": total - unsynced,
            "db_size_mb": round(db_size, 2),
        },
        "mqtt": {
            "connected": _publisher.is_connected() if _publisher else False,
        },
        "sync": {
            "backlog": unsynced,
        },
        "signals": len(_config.get("signals", [])),
        "version": "0.2.0",
    })


async def handle_latest(request):
    """Latest value per signal (current snapshot)."""
    rows = _buffer.conn.execute("""
        SELECT signal_id, value, quality, MAX(ts) as ts
        FROM measurements
        GROUP BY signal_id
        ORDER BY signal_id
    """).fetchall()

    return web.json_response([
        {"signal_id": r[0], "value": r[1], "quality": r[2], "timestamp": r[3].isoformat() if r[3] else None}
        for r in rows
    ])


async def handle_recent(request):
    """50 most recent measurements."""
    limit = int(request.query.get("limit", "50"))
    rows = _buffer.conn.execute("""
        SELECT ts, signal_id, value, quality
        FROM measurements
        ORDER BY ts DESC LIMIT ?
    """, [limit]).fetchall()

    return web.json_response([
        {"timestamp": r[0].isoformat() if r[0] else None, "signal_id": r[1], "value": r[2], "quality": r[3]}
        for r in rows
    ])


async def handle_config(request):
    """Current config (sanitized — no passwords)."""
    cfg = dict(_config)
    # Remove sensitive fields if any
    return web.json_response(cfg)


async def handle_index(request):
    """Serve inline HTML dashboard."""
    html = """
    <!DOCTYPE html><html lang="en"><head><meta charset="UTF-8">
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <title>PlantOS Edge Agent</title>
    <style>
      *{margin:0;padding:0;box-sizing:border-box}
      body{background:#0f172a;color:#e2e8f0;font-family:monospace;padding:20px}
      h1{font-size:18px;margin-bottom:16px;border-bottom:1px solid #1e293b;padding-bottom:8px}
      .grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:12px;margin-bottom:20px}
      .card{background:#1e293b;border:1px solid #334155;border-radius:8px;padding:14px}
      .card .label{font-size:11px;color:#94a3b8;text-transform:uppercase}
      .card .value{font-size:24px;font-weight:bold;margin-top:4px}
      .card .value.green{color:#22c55e}.card .value.yellow{color:#f59e0b}.card .value.red{color:#ef4444}
      table{width:100%;border-collapse:collapse;font-size:12px}
      th{text-align:left;padding:8px 12px;background:#1e293b;color:#94a3b8;font-weight:normal;border-bottom:1px solid #334155}
      td{padding:6px 12px;border-bottom:1px solid #1e293b}
      .badge{padding:1px 6px;border-radius:4px;font-size:10px}
      .badge.good{background:#166534;color:#22c55e}
      .badge.bad{background:#7f1d1d;color:#ef4444}
      .badge.simulated{background:#312e81;color:#8b5cf6}
      #updated{font-size:10px;color:#475569;margin-top:12px;text-align:right}
    </style></head><body>
    <h1>🏭 PlantOS Edge Agent</h1>
    <div class="grid" id="stats"></div>
    <h1>📡 Latest Values</h1>
    <table><thead><tr><th>Signal ID</th><th>Value</th><th>Quality</th><th>Timestamp</th></tr></thead><tbody id="latest"></tbody></table>
    <div id="updated">Auto-refresh: 5s</div>
    <script>
      async function load() {
        try {
          const s = await fetch('/api/status').then(r=>r.json());
          document.getElementById('stats').innerHTML = `
            <div class="card"><div class="label">Uptime</div><div class="value green">${Math.floor(s.uptime_seconds/60)}m</div></div>
            <div class="card"><div class="label">DB Rows</div><div class="value">${s.duckdb.total_rows.toLocaleString()}</div></div>
            <div class="card"><div class="label">Unsynced</div><div class="value ${s.duckdb.unsynced>0?'yellow':'green'}">${s.duckdb.unsynced}</div></div>
            <div class="card"><div class="label">MQTT</div><div class="value ${s.mqtt.connected?'green':'red'}">${s.mqtt.connected?'ON':'OFF'}</div></div>
            <div class="card"><div class="label">Signals</div><div class="value">${s.signals}</div></div>
            <div class="card"><div class="label">DB Size</div><div class="value">${s.duckdb.db_size_mb} MB</div></div>
          `;
          const l = await fetch('/api/measurements/latest').then(r=>r.json());
          document.getElementById('latest').innerHTML = l.map(m=>`
            <tr><td style="font-size:11px">${m.signal_id}</td>
            <td>${m.value!=null?m.value:'—'}</td>
            <td><span class="badge ${(m.quality||'').toLowerCase()}">${m.quality||'—'}</span></td>
            <td style="font-size:10px;color:#64748b">${m.timestamp?new Date(m.timestamp).toLocaleTimeString():'—'}</td></tr>
          `).join('');
          document.getElementById('updated').textContent = 'Updated: ' + new Date().toLocaleTimeString();
        } catch(e) { console.error(e); }
      }
      load(); setInterval(load, 5000);
    </script></body></html>"""
    return web.Response(text=html, content_type="text/html")


def create_app():
    app = web.Application()
    app.router.add_get("/", handle_index)
    app.router.add_get("/api/status", handle_status)
    app.router.add_get("/api/measurements/latest", handle_latest)
    app.router.add_get("/api/measurements/recent", handle_recent)
    app.router.add_get("/api/config", handle_config)
    return app


async def run_server(host="0.0.0.0", port=8001):
    app = create_app()
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host, port)
    await site.start()
    print(f"Edge Web UI: http://{host}:{port}")
```

### 3. `edge/agent/main.py` — Integrate Web Server

Thêm vào `EdgeAgent.__init__`:

```python
from web import setup as web_setup, run_server

# In __init__, after creating buffer/publisher/sync:
web_setup(self.buffer, self.mqtt, self.sync, self.cfg)
```

Thêm vào `EdgeAgent.run()`:

```python
# Start web server as background task
asyncio.create_task(run_server(port=8001))
```

### 4. `frontend/src/features/edge-fleet/EdgeFleetPage.tsx` — Detail Panel

Thêm state `selectedNode`, khi click row → set selectedNode → hiển thị panel bên phải fetch từ Edge API:

```tsx
const [selectedNode, setSelectedNode] = useState<string | null>(null);

// When row clicked:
onClick={() => setSelectedNode(n.edge_node_id)}

// Detail panel:
{selectedNode && (
  <div className="w-80 bg-gray-900 border-l border-gray-800 p-4 space-y-4">
    <h3 className="font-bold">{selectedNode}</h3>
    <EdgeNodeDetail nodeId={selectedNode} />
  </div>
)}
```

```tsx
function EdgeNodeDetail({ nodeId }: { nodeId: string }) {
  const { data: status } = useQuery({
    queryKey: ["edge-status", nodeId],
    queryFn: () => fetch(`http://localhost:8001/api/status`).then(r => r.json()),
    refetchInterval: 5000,
  });

  if (!status) return <div className="text-gray-500">Loading...</div>;

  return (
    <div className="space-y-3 text-sm">
      <div><span className="text-gray-500">Uptime:</span> {Math.floor(status.uptime_seconds / 60)}m</div>
      <div><span className="text-gray-500">DB Rows:</span> {status.duckdb.total_rows}</div>
      <div><span className="text-gray-500">Unsynced:</span> <span className={status.duckdb.unsynced > 0 ? "text-yellow-400" : "text-green-400"}>{status.duckdb.unsynced}</span></div>
      <div><span className="text-gray-500">MQTT:</span> <span className={status.mqtt.connected ? "text-green-400" : "text-red-400"}>{status.mqtt.connected ? "Connected" : "Disconnected"}</span></div>
      <div><span className="text-gray-500">Signals:</span> {status.signals}</div>
      <div><span className="text-gray-500">DB Size:</span> {status.duckdb.db_size_mb} MB</div>
      <a href="http://localhost:8001" target="_blank" className="text-blue-400 text-xs">Open Edge Dashboard →</a>
    </div>
  );
}
```

## Constraints

- [x] Web server chạy trên cùng event loop với agent (aiohttp, không process riêng)
- [x] Dashboard HTML inline — không React, không build step
- [x] Auto-refresh 5s qua JavaScript setInterval
- [x] Tất cả API endpoints trả JSON

## Validation

```bash
# 1. Start edge agent
cd edge/agent && pip install -r requirements.txt && python main.py

# 2. Open dashboard
open http://localhost:8001

# 3. Check status API
curl http://localhost:8001/api/status

# 4. Check Center Fleet UI → click node → detail panel
open http://localhost:5173/edge
```

## Về Protocol Adapters + Asset Sync

| Chức năng | Plan |
|---|---|
| ModbusTCP, OPC UA | **Defer 3-03** — thêm `edge/collectors/` module |
| Asset sync Center→Edge | **Defer 3-02** — API endpoint + Edge downloader |
| Edge setup/config UI | **Hiện tại** — xem config qua `/api/config`, sửa qua `config.yaml` |
