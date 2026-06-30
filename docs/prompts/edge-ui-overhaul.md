# Edge UI Overhaul — Simplified Center Design

> **Designer:** DeepSeek V4 Pro | **Date:** 2026-06-30

## Context

Edge UI cần match Center design system nhưng đơn giản hóa — chỉ giữ Dashboard, Assets, Connections. Dùng HTML + inline CSS (không React), cùng design tokens với Center.

## Design System (Shared with Center)

```css
:root {
  --bg-primary: #0f172a;
  --bg-card: #1e293b;
  --border: #334155;
  --text-primary: #e2e8f0;
  --text-muted: #94a3b8;
  --accent: #3b82f6;
  --status-good: #22c55e;
  --status-warn: #f59e0b;
  --status-alarm: #ef4444;
  --status-offline: #6b7280;
  --radius: 8px;
  --font-mono: 'Consolas', 'Courier New', monospace;
}
```

## Layout

```
┌──────────────────────────────────────────────────────────┐
│  🏭 PlantOS Edge Agent    [📊 Dashboard] [🏭 Assets] [🔌 Connections] │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  ┌─────────┐ ┌─────────┐ ┌──────────┐ ┌─────────┐      │
│  │ UPTIME  │ │ DB ROWS │ │ UNSYNCED │ │  MQTT   │      │
│  │  45m 🟢 │ │ 15,230  │ │   0 🟢   │ │  ON 🟢  │      │
│  └─────────┘ └─────────┘ └──────────┘ └─────────┘      │
│                                                          │
│  📡 Latest Values                    auto-refresh 5s    │
│  ┌──────────────────┬───────────┬─────────┬──────────┐  │
│  │ Signal ID        │ Value     │ Quality │ Time     │  │
│  ├──────────────────┼───────────┼─────────┼──────────┤  │
│  │ PUMP-101.press.. │ 7.2 bar   │ 🟣 SIM  │ 16:40:01 │  │
│  │ PUMP-101.flow    │ 100.5 m³/h│ 🟣 SIM  │ 16:40:01 │  │
│  └──────────────────┴───────────┴─────────┴──────────┘  │
│                                                          │
│  Edge Agent v0.2.0  |  Synced: 9 assets, 15 signals     │
└──────────────────────────────────────────────────────────┘
```

## Implementation Checklist

- [ ] FIX `edge/agent/web.py` — /api/status + /api/measurements/latest bugs
- [ ] REWRITE `edge/agent/templates/dashboard.html` — full overhaul with Center design
- [ ] CREATE `edge/agent/web.py` route for tab switching (single HTML with JS tabs)
- [ ] ADD `/api/assets` endpoint — serve synced manifest assets
- [ ] ADD `/api/connections` endpoint — MQTT + Modbus + sync status

## Detailed Instructions

### 1. Fix API Endpoints in `web.py`

Fix `/api/status` — handle case where _buffer might be None or DuckDB not initialized:

```python
async def handle_status(request):
    try:
        conn = _buffer.conn
        total = conn.execute("SELECT COUNT(*) FROM measurements").fetchone()[0]
        unsynced = _buffer.count_unsynced()
        db_path = Path(_buffer.path)
        db_size = db_path.stat().st_size / (1024*1024) if db_path.exists() else 0
    except Exception:
        total, unsynced, db_size = 0, 0, 0

    return web.json_response({
        "node_id": _config.get("edge_node_id", "unknown"),
        "uptime_seconds": int(time.time() - start_time),
        "duckdb": {"total_rows": total, "unsynced": unsynced, "db_size_mb": round(db_size, 2)},
        "mqtt": {"connected": _publisher.is_connected() if _publisher else False},
        "modbus": {
            "enabled": _modbus_collector is not None,
            "connected": _modbus_collector.connected if _modbus_collector else False,
            "host": _modbus_collector.client.host if _modbus_collector else None,
            "tags": len(_modbus_collector.mapper.tags) if _modbus_collector else 0,
        } if _modbus_collector else {"enabled": False},
        "sync": {"backlog": unsynced},
        "signals": len(_config.get("signals", [])),
        "version": "0.2.0",
    })
```

Fix `/api/measurements/latest`:

```python
async def handle_latest(request):
    try:
        rows = _buffer.conn.execute("""
            SELECT signal_id, value, quality, MAX(ts) as ts
            FROM measurements GROUP BY signal_id ORDER BY signal_id
        """).fetchall()
        return web.json_response([
            {"signal_id": r[0], "value": r[1], "quality": r[2] or "SIMULATED",
             "timestamp": r[3].isoformat() if r[3] else None}
            for r in rows
        ])
    except Exception:
        return web.json_response([])
```

Add `/api/assets`:

```python
async def handle_assets(request):
    """Return synced assets from metadata manager."""
    try:
        manifest = _metadata.manifest if hasattr(_metadata, 'manifest') else {}
        return web.json_response(manifest.get("assets", []))
    except Exception:
        return web.json_response([])
```

### 2. Full Dashboard HTML Overhaul

Single HTML file with tab navigation, CSS tokens matching Center, responsive grid, stats cards, and data tables.

> Coder viết toàn bộ HTML trong `templates/dashboard.html` với:
> - **CSS**: Dùng design tokens ở trên, font Inter/system-ui cho text, monospace cho data
> - **Tabs**: 3 tabs (Dashboard, Assets, Connections) bằng JS show/hide
> - **Dashboard tab**: 4 stat cards (uptime, DB rows, unsynced, MQTT) + latest values table
> - **Assets tab**: Table hiển thị synced assets từ `/api/assets` (asset_id, name, type, status)
> - **Connections tab**: 
>   - MQTT: host, port, status indicator
>   - Modbus: enabled/disabled, host, port, tag count
>   - Sync: backlog count, Center URL
>   - HTTP ingest: configured URL
> - **Footer**: version + sync status
> - **Auto-refresh**: 5s cho dashboard tab, manual refresh cho assets/connections

### 3. Setup Page Enhancement

Cập nhật `templates/setup.html` với cùng design system — navigation tabs, form styling matching Center.

## Files

| # | File | Action |
|---|------|--------|
| 1 | `edge/agent/web.py` | MODIFY — fix APIs + add /api/assets |
| 2 | `edge/agent/templates/dashboard.html` | REWRITE — full overhaul |
| 3 | `edge/agent/templates/setup.html` | MODIFY — matching design |

## Reference: Center Colors

```css
/* Same as Center Tailwind config */
bg-gray-950  → #0f172a    bg-gray-900   → #1e293b
border-gray-800 → #1e293b border-gray-700 → #334155
text-gray-100 → #e2e8f0  text-gray-400   → #94a3b8
text-gray-500 → #64748b  accent-blue     → #3b82f6
```

## Validation

```bash
# 1. Start Edge Agent
cd edge/agent && python main.py

# 2. Open in browser
open http://localhost:8001

# 3. Verify: tabs switch, stats load, assets table populates
# 4. Verify: design matches Center (dark theme, same fonts, same radius)
```
