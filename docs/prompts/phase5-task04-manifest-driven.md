# Phase 5 — Task 5-04: Manifest-Driven Seed + Edge OPC UA Binding

> **Designer:** DeepSeek V4 Pro | **Date:** 2026-07-01
> **Prerequisite:** ADR-0005, `examples/vf-plantos-contract.yaml`

## Context

Hiện tại seed data và Edge OPC UA config được hardcode độc lập. Theo ADR-0005, mọi thứ phải đến từ 1 manifest duy nhất `examples/vf-plantos-contract.yaml`.

## Goals

1. Seed script đọc manifest → tạo asset/signal qua API
2. Edge mapper đọc manifest từ Center sync → tự động build OPC UA binding
3. `config.yaml` không còn hardcode `opcua.tags[]`

## Implementation Checklist

- [ ] MODIFY `backend/app/seed/vf_demo_plant.py` — đọc từ `examples/vf-plantos-contract.yaml`
- [ ] MODIFY `edge/agent/collectors/opcua/mapper.py` — build mapping từ manifest
- [ ] MODIFY `edge/agent/collectors/opcua/collector.py` — nhận manifest qua constructor
- [ ] MODIFY `edge/agent/main.py` — truyền metadata manifest vào collector
- [ ] MODIFY `edge/agent/config.yaml` — xóa `opcua.tags[]`, chỉ giữ endpoint + poll interval

## Detailed Instructions

### 1. `backend/app/seed/vf_demo_plant.py` (MODIFY)

Thay thế toàn bộ content bằng script đọc manifest:

```python
"""Seed data from Integration Data Contract manifest.

Reads examples/vf-plantos-contract.yaml and creates Plant, Area, Assets, and Signals.
Idempotent — skips entities that already exist.
"""

import yaml
from pathlib import Path

MANIFEST_PATH = Path(__file__).resolve().parents[3] / "examples" / "vf-plantos-contract.yaml"


def load_manifest() -> dict:
    """Load the integration contract manifest."""
    with open(MANIFEST_PATH) as f:
        return yaml.safe_load(f)


def seed_from_manifest():
    """Seed PlantOS Center from the integration manifest."""
    from app.modules.assets.schemas import PlantCreate, AreaCreate, AssetCreate
    from app.modules.assets.service import PlantService, AreaService, AssetService
    from app.modules.signals.schemas import SignalCreate, SourceInfo
    from app.modules.signals.service import SignalService

    manifest = load_manifest()
    plant_svc = PlantService()
    area_svc = AreaService()
    asset_svc = AssetService()
    signal_svc = SignalService()
    results = {"plants": 0, "areas": 0, "assets": 0, "signals": 0, "skipped": 0}

    # Plant
    p = manifest["plant"]
    try:
        plant_svc.create_plant(PlantCreate(
            plant_id=p["plant_id"], name=p["name"],
            timezone="UTC", status="active",
        ))
        results["plants"] += 1
    except ValueError:
        results["skipped"] += 1

    # Areas
    for a in manifest.get("areas", []):
        try:
            area_svc.create_area(AreaCreate(
                area_id=a["area_id"], plant_id=a["plant_id"],
                name=a["name"], area_type=None, status="active",
            ))
            results["areas"] += 1
        except ValueError:
            results["skipped"] += 1

    # Assets (giữ nguyên thứ tự — parent trước children)
    for a in manifest.get("assets", []):
        try:
            asset_svc.create_asset(AssetCreate(
                asset_id=a["asset_id"], asset_code=a.get("asset_code", a["asset_id"]),
                name=a["name"], asset_type=a["asset_type"],
                parent_asset_id=a.get("parent_asset_id"),
                plant_id=a.get("plant_id"), area_id=a.get("area_id"),
                criticality=a.get("criticality", "medium"),
            ))
            results["assets"] += 1
        except ValueError:
            results["skipped"] += 1

    # Signals
    for s in manifest.get("signals", []):
        try:
            src = SourceInfo(source_type="opcua", source_ref=s["opcua_node_id"])
            signal_svc.create_signal(SignalCreate(
                signal_id=s["signal_id"], asset_id=s["asset_id"],
                signal_name=s["signal_name"],
                display_name=s.get("display_name"),
                signal_type=s.get("signal_type", "measurement"),
                data_type=s.get("data_type", "float"),
                engineering_unit=s.get("engineering_unit"),
                source=src,
            ))
            results["signals"] += 1
        except ValueError:
            results["skipped"] += 1

    return results
```

Cập nhật `api/v1.py` seed endpoint:

```python
@router.post("/seed/vf-demo", tags=["Seed"])
def seed_vf_demo():
    from app.seed.vf_demo_plant import seed_from_manifest
    try:
        results = seed_from_manifest()
        return {"status": "ok", **results}
    except Exception as e:
        return {"status": "error", "message": str(e)}
```

### 2. `edge/agent/collectors/opcua/mapper.py` (MODIFY)

Thêm method `from_manifest()`:

```python
class OpcUaMapper:
    """Maps OPC UA NodeIds to PlantOS signal_ids."""

    def __init__(self, tags: list[dict] = None):
        self.mappings: list[SignalMapping] = []
        if tags:
            for tag in tags:
                self.mappings.append(SignalMapping(
                    node_id=tag["node_id"],
                    signal_id=tag["signal_id"],
                    scale=tag.get("scale", 1.0),
                    offset=tag.get("offset", 0.0),
                ))

    @classmethod
    def from_manifest(cls, manifest: dict):
        """Build mapper from Center-synced manifest.

        Only includes signals with source_type='opcua'.
        """
        mapper = cls(tags=[])
        for s in manifest.get("signals", []):
            source = s.get("source") or {}
            if source.get("source_type") == "opcua":
                mapper.mappings.append(SignalMapping(
                    node_id=source["source_ref"],
                    signal_id=s["signal_id"],
                    scale=s.get("scale", 1.0),
                ))
        return mapper

    # ... rest unchanged
```

### 3. `edge/agent/collectors/opcua/collector.py` (MODIFY)

Thay đổi constructor để nhận mapper trực tiếp (không tự tạo từ tags):

```python
class OpcUaCollector:
    def __init__(self, config: dict, buffer, mapper: OpcUaMapper = None):
        self.config = config
        self.buffer = buffer
        self.client = OpcUaClient(
            endpoint=config.get("endpoint", "opc.tcp://127.0.0.1:4840"),
            timeout=config.get("timeout", 5.0),
        )
        self.mapper = mapper or OpcUaMapper(config.get("tags", []))
        self.interval = config.get("poll_interval_ms", 1000) / 1000
        self._enabled = config.get("enabled", False)
        self._task: asyncio.Task | None = None
    # ... rest unchanged
```

### 4. `edge/agent/main.py` (MODIFY)

Trong `EdgeAgent.__init__`, thay đổi cách tạo OpcUaCollector:

```python
        # OPC UA collector — build mapper from Center manifest
        from collectors.opcua import OpcUaCollector
        from collectors.opcua.mapper import OpcUaMapper

        opcua_cfg = self.cfg.get("opcua", {})
        opcua_mapper = OpcUaMapper.from_manifest(
            self.metadata.manifest
        ) if self.metadata.manifest.get("signals") else OpcUaMapper([])

        self.opcua_collector = OpcUaCollector(opcua_cfg, self.buffer, opcua_mapper)
```

> **Lưu ý:** `self.metadata.sync()` phải chạy TRƯỚC khi tạo `opcua_collector`. Nếu Center chưa sẵn sàng, fallback load từ cache.

### 5. `edge/agent/config.yaml` (MODIFY)

Xóa toàn bộ `tags[]`:

```yaml
# OPC UA collector (Virtual Factory Compressor Train)
opcua:
  enabled: true
  endpoint: opc.tcp://localhost:4840
  timeout: 5.0
  poll_interval_ms: 1000
  # tags[] đã chuyển sang examples/vf-plantos-contract.yaml
  # Mapper tự động build từ Center manifest
```

---

## Validation

```bash
# 1. Verify manifest parseable
python -c "import yaml; yaml.safe_load(open('examples/vf-plantos-contract.yaml')); print('OK')"

# 2. Re-seed Center
curl -X POST http://localhost:8000/api/v1/seed/vf-demo
# → {"status":"ok","plants":1,"areas":1,"assets":7,"signals":26,"skipped":7}

# 3. Restart Edge Agent
cd edge/agent && python main.py
# Log: OPC UA collector started (26 signals) — from manifest

# 4. Verify OPC UA data
curl http://localhost:8001/api/status
# → opcua.connected=true, signal_count=26

# 5. Verify Center data
curl "http://localhost:8000/api/v1/measurements/current?asset_id=COMP01-CORE"
# → 7 signals with values
```

---

## Files Summary

| # | File | Action | Description |
|---|------|--------|-------------|
| 1 | `backend/app/seed/vf_demo_plant.py` | MODIFY | Đọc từ manifest YAML |
| 2 | `edge/agent/collectors/opcua/mapper.py` | MODIFY | Thêm `from_manifest()` |
| 3 | `edge/agent/collectors/opcua/collector.py` | MODIFY | Nhận mapper qua constructor |
| 4 | `edge/agent/main.py` | MODIFY | Build mapper từ metadata sync |
| 5 | `edge/agent/config.yaml` | MODIFY | Xóa `tags[]` |

## Handoff to Coder

```
Đọc: docs/prompts/phase5-task04-manifest-driven.md
5 files MODIFY. Seed đọc manifest. Edge mapper từ Center sync.
Không hardcode signal_id trong config.yaml nữa.
Validate: seed → restart Edge → OPC UA vẫn đọc được 26 signals.
```
