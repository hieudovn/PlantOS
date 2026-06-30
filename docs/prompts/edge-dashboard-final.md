# Edge Dashboard — Signal Values + Connection Setup + Asset Tree

> **Designer:** DeepSeek V4 Pro | **Date:** 2026-06-30

## Context

3 gaps cần fix:
1. Dashboard thiếu signal values (có API `/api/measurements/latest` nhưng không hiển thị)
2. Connections page thiếu setup form (Modbus config)
3. Assets page phẳng — cần tree hierarchy + click detail

Tất cả trong `dashboard.html` + `web.py`.

## Implementation Checklist

- [ ] MODIFY `edge/agent/templates/dashboard.html` — signal cards + connection form + asset tree
- [ ] MODIFY `edge/agent/web.py` — add connection save endpoint

## Detailed Instructions

### 1. Dashboard — Signal Value Cards

Thay vì chỉ có table, thêm grid cards cho mỗi signal (fetch từ `/api/measurements/latest`):

```
📡 Signal Values
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ PUMP-101     │ │ PUMP-101     │ │ MOTOR-101    │
│ pressure     │ │ flow_rate    │ │ current      │
│              │ │              │ │              │
│   7.2 bar    │ │ 100.5 m³/h  │ │   45.8 A     │
│   🟣 SIM     │ │   🟣 SIM     │ │   🟣 SIM     │
└──────────────┘ └──────────────┘ └──────────────┘
```

HTML/CSS: grid `grid-template-columns: repeat(auto-fill, minmax(180px, 1fr))` với mỗi card hiển thị: signal name, value + unit, quality badge.

### 2. Connections — Inline Modbus Form

Tab Connections hiện tại chỉ show status. Thêm form:

```
🔌 Connections
  
  MQTT:
  Host: localhost:1883    Status: ● Disconnected (EMQX not running)

  Modbus TCP:
  ┌─────────────────────────────────────────────────────┐
  │ Host: [127.0.0.1]  Port: [502]  Unit ID: [1]      │
  │ Poll Interval: [1000] ms                            │
  │                                                     │
  │ Tags:                        [+ Add]                │
  │ ┌──────────┬────────┬──────────────────────────┐   │
  │ │ Register │ Type   │ Signal ID                │   │
  │ │ 40001    │ holding│ PUMP-101.discharge_press  │   │
  │ └──────────┴────────┴──────────────────────────┘   │
  │                                                     │
  │ [Save Config]  Status: ● Disabled                   │
  └─────────────────────────────────────────────────────┘
```

Form submit → POST `/api/connections/save` → ghi vào `config.yaml`.

### 3. Assets — Tree Hierarchy

Dùng `parent_asset_id` từ manifest để build cây:

```
🏭 Assets (9)
  
🌳 DEMO-PLANT
├── 📁 PROCESS-AREA
│   └── 📦 LINE-01
│       ├── 🔧 PUMP-101        🟢 active  [detail ▸]
│       ├── ⚡ MOTOR-101        🟢 active  [detail ▸]
│       ├── 🛢️ TANK-101         🟢 active  [detail ▸]
│       └── 🔩 VALVE-101        🟢 active  [detail ▸]
└── 📁 ELECTRICAL-AREA
    └── 🏭 SUBSTATION-A
        ├── 🔌 TRANSFORMER-01   🟢 active
        ├── ⚡ FEEDER-01        🟢 active
        └── 🔒 BREAKER-01      🟢 active
```

Click [detail ▸] → expand inline panel hiển thị asset metadata + signal list.

### 4. API — Save Connection Config

```python
async def handle_save_connection(request):
    """Save Modbus connection config to YAML."""
    try:
        data = await request.json()
        # Update in-memory config
        if "modbus" not in _config:
            _config["modbus"] = {}
        _config["modbus"].update(data.get("modbus", {}))
        # Save to YAML file
        import yaml
        with open("config.yaml", "w") as f:
            yaml.dump(_config, f, default_flow_style=False)
        return web.json_response({"status": "saved"})
    except Exception as e:
        return web.json_response({"status": "error", "message": str(e)}, status=500)
```

Add route: `app.router.add_post("/api/connections/save", handle_save_connection)`

## Files

| # | File | Action |
|---|------|--------|
| 1 | `edge/agent/templates/dashboard.html` | MODIFY — signal cards + connection form + asset tree |
| 2 | `edge/agent/web.py` | MODIFY — connection save endpoint |

## Validation

```bash
# Restart agent, open http://localhost:8001
# 1. Dashboard: signal value cards visible with real values
# 2. Connections: Modbus form editable, Save persists to YAML
# 3. Assets: nested tree with click-to-expand detail
```
