# ADR-0005: Integration Data Contract (Virtual Factory ↔ PlantOS)

## Status

Proposed

## Context

Virtual Factory và PlantOS hiện định nghĩa asset model + signal mapping độc lập ở 3 nơi:

1. `virtual-factory/configs/plants/compressor_train_benchmark_01.yaml` — VF định nghĩa sensors, signals, OPC UA output
2. `plantos/edge/agent/config.yaml` — Edge định nghĩa OPC UA NodeId → signal_id mapping
3. `plantos/backend/app/seed/vf_demo_plant.py` — Center định nghĩa asset tree + signals

Không có liên kết giữa 3 nơi. Thay đổi 1 tín hiệu cần sửa thủ công cả 3 file.

## Decision

### 1. Integration Manifest — Single Source of Truth

Tạo file YAML duy nhất `examples/vf-plantos-contract.yaml` định nghĩa:

- **Plant**: plant_id, name
- **Areas**: area_id, name
- **Assets**: asset tree hierarchy (parent-child)
- **Signals**: signal_id, asset binding, OPC UA NodeId, unit conversion, VF sensor ref

### 2. Manifest làm nguồn sinh cấu hình

| Bên | Sinh ra |
|---|---|
| **PlantOS Center** | Seed script đọc manifest → tạo asset/signal qua API |
| **PlantOS Edge** | Mapper đọc manifest từ Center sync → tự động build NodeId→signal_id |
| **Virtual Factory** | Validate script kiểm tra VF config có đủ sensors khớp manifest |

### 3. Cấu trúc Manifest

```yaml
contract:
  version: "1.0"
plant:
  plant_id: VF-DEMO
areas: [...]
assets: [...]        # asset tree với parent-child
signals:             # mỗi signal có đủ thông tin cho cả 3 bên
  - signal_id: ...   # PlantOS CDM identifier
    opcua_node_id: ...  # OPC UA binding
    scale: ...        # unit conversion (Edge mapper)
    vf_sensor_id: ... # VF sensor reference (để validate)
```

### 4. Edge không tự định nghĩa signal_id nữa

`config.yaml` chỉ còn:
```yaml
opcua:
  enabled: true
  endpoint: opc.tcp://localhost:4840
  poll_interval_ms: 1000
  # tags[] REMOVED — mapper đọc từ Center manifest
```

Mapper nhận manifest từ `MetadataManager` và tự động build mapping:
```
for signal in manifest.signals:
    if signal.source_type == "opcua":
        add_mapping(signal.source_ref, signal.signal_id, signal.scale)
```

## Consequences

- ✅ 1 file duy nhất định nghĩa integration contract
- ✅ Thay đổi tín hiệu: sửa 1 dòng YAML → cả 2 hệ thống cập nhật
- ✅ Edge không hardcode signal_id — mọi thứ từ Center manifest
- ✅ VF có thể validate config khớp contract
- ✅ Tái sử dụng được cho mọi plant model khác (không chỉ Compressor Train)
- ⚠️ Cần script/code sinh cấu hình từ manifest (không phải manual)
