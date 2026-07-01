# VF Task: Validate & Sync with PlantOS Integration Contract

> **For:** Virtual Factory AI Assistant
> **Date:** 2026-07-01
> **Contract:** `PlantOS/examples/vf-plantos-contract.yaml`

## Context

PlantOS và Virtual Factory đã thống nhất Integration Data Contract tại file:

```
D:\Project\Github\PlantOS\examples\vf-plantos-contract.yaml
```

File này là **single source of truth** cho asset model và signal mapping giữa 2 hệ thống.

Virtual Factory cần đọc file này để:
1. Validate VF config có đủ sensors cho tất cả signals trong contract
2. Nếu thiếu → bổ sung sensors/signals vào VF plant config
3. Đảm bảo OPC UA output khớp contract

## Yêu Cầu

### 1. Đọc Contract

Đọc `D:\Project\Github\PlantOS\examples\vf-plantos-contract.yaml`. File chứa:
- `signals[].opcua_node_id` — NodeId mà PlantOS Edge mong đợi
- `signals[].vf_sensor_id` — Sensor ID trong VF config (vd: PT101, FT101)
- `signals[].vf_internal_ref` — Internal truth path (vd: COMP01.suction_pressure_kpa)

### 2. Validate VF Config

So sánh contract với VF config `configs/plants/compressor_train_benchmark_01.yaml`:

```
for each signal in contract:
    check: VF config có sensor với id = signal.vf_sensor_id?
    check: Sensor đo đúng internal_ref = signal.vf_internal_ref?
    check: Signal publish = true trong VF config?
    check: OPC UA output signal name khớp với opcua_node_id suffix?
```

### 3. Bổ Sung Nếu Thiếu

Nếu VF config thiếu sensor hoặc signal so với contract:
- Thêm sensor/transmitter definition
- Thêm signal definition với `publish: true`
- Đảm bảo category = "industrial_signal"

### 4. Test OPC UA

Sau khi cập nhật, chạy VF với `--opcua-endpoint` và browse để xác nhận đủ 26 signals trong contract:

```bash
virtual-factory run --config configs/plants/compressor_train_benchmark_01.yaml --steps 0 --dt 1.0 --opcua-endpoint opc.tcp://0.0.0.0:4840
```

Dùng UaExpert hoặc script Python browse OPC UA server để verify.

## Deliverables

| # | Output | Mô tả |
|---|--------|-------|
| 1 | `scripts/validate-contract.py` | Script validate VF config khớp contract |
| 2 | Cập nhật `compressor_train_benchmark_01.yaml` | Bổ sung sensors/signals nếu thiếu |
| 3 | Validation report | Report kết quả validate (pass/fail từng signal) |

## Integration Contract Summary

```
Plant: VF-DEMO
Assets: 7 (COMP01 + 6 sub-systems)
Signals: 26 (7 Core + 7 Motor + 6 Bearings + 3 Lube + 2 Cooling + 1 Seal)
OPC UA: ns=2 namespace, opc.tcp://0.0.0.0:4840
Unit conversions: chỉ flow_rate (m3/s ×3600 → m3/h)
```
