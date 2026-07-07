# PlantOS Center — Process View Upgrade Plan

> **Author:** PM-Designer | **Date:** 2026-07-07  
> **Source:** SA Proposal "Nâng cấp Diagram thành Process View trong PlantOS Center"  
> **Status:** SA APPROVED. Ready for Phase 6-PV-01.
> **Parent Phase:** Phase 6 (Industrial Hardening), per `docs/90-roadmap.md`

---

## 1. Executive Summary

Nâng cấp module `Diagrams` thành **Operations / Process View Workspace** — một không gian giám sát vận hành phân cấp với drill-down từ toàn nhà máy tới từng tín hiệu.

```text
Hiện tại: Diagrams = 1 trang hiển thị SVG tĩnh, 1 diagram/plant, binding YAML thủ công
Tương lai: Operations = workspace đa cấp Plant → Area → Asset → Signal với overlay/breadcrumb
```

---

## 2. Information Architecture

### 2.1 Navigation

```text
Sidebar:
  MONITOR
    Overview             → /               (giữ nguyên)
    Operations           → /operations     (MỚI — thay /diagrams)
    Historian            → /historian      (giữ nguyên)
    Alarms               → /alarms         (giữ nguyên)

  MANAGEMENT
    Reports              → /reports

  PLATFORM
    Assets               → /assets
    Signals              → /signals
    Edge Fleet           → /edge
    System               → /system
    Users                → /users
```

**Route mapping:**
- `/diagrams` → redirect 301 đến `/operations` (backward compat)
- `/operations` → ProcessViewWorkspace (route chính)
- `/operations/area/:areaId` → Area View
- `/operations/asset/:assetId` → Asset Condition View

### 2.2 View Hierarchy

```text
Level 1: Plant Overview          → /operations
Level 2: Area / Process View     → /operations/area/:areaId
Level 3: Asset Condition View    → /operations/asset/:assetId
Level 4: Signal Investigation    → link qua Historian với ?signal=ID
```

---

## 3. UI Layout Design

### 3.1 Workspace Shell

```
┌──────────────────────────────────────────────────────────┐
│ Breadcrumb: WTP-DEMO-01 > Filtration Area > FILTER-101   │
├────────────┬─────────────────────────────┬───────────────┤
│ Hierarchy  │                             │  Context      │
│ Panel      │    Main Canvas              │  Panel        │
│            │                             │               │
│ ▼ Plant    │  workflow / P&ID / asset    │  KPI cards    │
│   ▼ Area   │  condition diagram          │  Trend bundle │
│     Asset  │                             │  Alarm list   │
│     Asset  │                             │  Events       │
│            │                             │               │
├────────────┴─────────────────────────────┴───────────────┤
│ Overlay Bar: [Status] [Alarm] [Quality] [Energy] [Risk]  │
└──────────────────────────────────────────────────────────┘
```

- **Header:** Breadcrumb + plant/area/asset name + data freshness indicator
- **Left panel (240px):** Hierarchy tree, collapsible. Filter by status/criticality
- **Main canvas:** Flex area — adapts to view type (workflow blocks, P&ID SVG, asset panel)
- **Right panel (320px, collapsible):** Context for selected object — KPI, trends, alarms
- **Overlay bar:** Toggle buttons cho status/alarm/quality/energy/risk overlays

### 3.2 Responsive note

Phase đầu chỉ desktop. Tablet/minimal support ở UI-D5+.

---

## 4. View Types

### 4.1 Plant Workflow Overview (Level 1)

**Dùng cho:** WTP-DEMO-01 plant overview

```text
┌────────┐   ┌────────┐   ┌────────┐   ┌────────┐   ┌────────┐   ┌────────┐   ┌────────┐
│ Intake │──▶│ Dosing │──▶│Clarifier│──▶│Filters │──▶│Disinf. │──▶│Storage │──▶│Distrib.│
│  ✅    │   │  ✅    │   │  ⚠️    │   │  ✅    │   │  ✅    │   │  ✅    │   │  ✅    │
│12.5 m3 │   │4.2 mg/L│   │3.2 NTU │   │0.3 NTU │   │1.2 mg/L│   │85%     │   │98%     │
│ 0 alarms│  │ 0      │   │ 2      │   │ 0      │   │ 0      │   │ 0      │   │ 0      │
└────────┘   └────────┘   └────────┘   └────────┘   └────────┘   └────────┘   └────────┘
```

Mỗi block là 1 Area/Process Unit. Click → drill-down Area View.

**Data source:** Area list từ `/api/v1/areas?plant_id=WTP-DEMO-01` + `/api/v1/measurements/current` cho KPI.

### 4.2 Area / Process View (Level 2)

**Dùng cho:** Filtration Area (ví dụ)

Hiển thị simplified process diagram với:
- Key assets trong area (từ API `/api/v1/assets?area_id=...`)
- Key signals per asset (từ asset_role=equipment, chọn 2-3 signal quan trọng nhất)
- Active alarms overlay (đèn đỏ trên asset block)
- Data quality indicator

### 4.3 Asset Condition View (Level 3)

**Dùng cho:** FILTER-101, HSP-101, CHLORINE-PUMP-101

```text
┌─────────────────────────────────────────────────┐
│ FILTER-101                     Status: ⚠️ Warning │
│ filter | equipment | Filtration Area              │
├──────────────────┬──────────────────────────────┤
│ Condition Score  │ Trend Bundle (last 24h)       │
│      72/100      │ [filter_dp] [filtered_turb.]  │
│   ⚠️ Degrading   │                              │
├──────────────────┴──────────────────────────────┤
│ Alarm Timeline                                  │
│ 12:00 ⚠️ DP High    13:30 ✅ DP Normal           │
└─────────────────────────────────────────────────┘
```

### 4.4 Signal Investigation (Level 4)

**Không xây mới.** Dùng Historian hiện có với deep-link `?signal=ID`. Process View mở Historian trong tab mới hoặc iframe.

---

## 5. Component Architecture

```
src/features/operations/
├── ProcessViewWorkspace.tsx     # Shell: layout + breadcrumb + routing
├── PlantOverviewView.tsx        # Level 1: workflow block diagram
├── AreaMonitoringView.tsx       # Level 2: area process diagram
├── AssetConditionView.tsx       # Level 3: asset condition panel
├── components/
│   ├── ProcessBlock.tsx         # 1 workflow block (Level 1)
│   ├── HierarchyPanel.tsx       # Left hierarchy tree
│   ├── OverlayBar.tsx           # Bottom overlay toggle bar
│   ├── ContextPanel.tsx         # Right context panel
│   └── BreadcrumbNav.tsx        # Top breadcrumb
├── config/
│   ├── wtp-workflow.ts          # WTP plant workflow config (temporary hardcode)
│   └── process-view-types.ts    # TypeScript types
└── hooks/
    ├── useProcessHierarchy.ts   # Fetch hierarchy from asset API
    └── useAssetCondition.ts     # Aggregate condition data
```

---

## 6. Data/Config Dependency List

| Dependency | Hiện có? | Ghi chú |
|-----------|:---:|---------|
| Asset list by plant/area | ✅ | `/api/v1/assets?plant_id=&area_id=` |
| Signal list by asset | ✅ | `/api/v1/signals?asset_id=` |
| Current values | ✅ | `/api/v1/measurements/current?signal_id=` |
| Asset hierarchy tree | ✅ | Asset API with parent_asset_id |
| Area list by plant | ✅ | `/api/v1/areas?plant_id=` |
| Plant workflow order | ❌ | Hardcode config UI-D1→D2, Contract Registry ở UI-D5 |
| Process relationships | ❌ | Static config, future KG |
| Condition score logic | ❌ | Simulated/threshold-based demo |
| Alarm rules engine | ⚠️ | Có infrastructure, chưa có rules |

---

## 7. Implementation Phases

### Phase 6-PV-01 — Rename & Workspace Foundation (3-4h)

```
1. Đổi sidebar label: "Diagrams" → "Operations" (icon: Factory thay Workflow)
2. Thêm route /operations → ProcessViewWorkspace
3. Redirect 301 /diagrams → /operations
4. ProcessViewWorkspace shell: breadcrumb + hierarchy panel (trái) + main canvas + context panel (phải) + overlay bar placeholder
5. Hierarchy panel: fetch areas/assets từ API, render tree
```

**Acceptance:**
- Sidebar hiển thị "Operations"
- `/diagrams` redirect về `/operations`
- `/operations` hiển thị shell với hierarchy tree bên trái
- Click node trong tree → breadcrumb cập nhật

### Phase 6-PV-02 — Plant Workflow Overview (3-4h)

```
1. PlantOverviewView: workflow block diagram cho WTP-DEMO-01
2. Hardcode 7 process blocks: Intake → Dosing → Clarifier → Filters → Disinfection → Storage → Distribution
3. Mỗi block bind KPI từ area signals (current value API)
4. Block status từ alarm count + data freshness
5. Click block → navigate đến Area View
```

**Acceptance:**
- 7 process blocks hiển thị cho WTP-DEMO-01
- Mỗi block có status icon, KPI value, alarm count
- Click block → URL đổi sang `/operations/area/:areaId`

### Phase 6-PV-03 — Area View (2-3h)

```
1. AreaMonitoringView cho 1 area (Filtration Area)
2. Simplified diagram: asset blocks + connections
3. Asset blocks với key signals (2-3 per asset)
4. Alarm overlay trên asset blocks
5. Click asset → navigate Asset Condition View
```

**Acceptance:**
- Filtration Area hiển thị filter assets + signals
- Alarm count hiển thị trên asset blocks
- Click asset → `/operations/asset/:assetId`

### Phase 6-PV-04 — Asset Condition View (3-4h)

```
1. AssetConditionView cho 3-5 asset
2. Condition score (simulated: dựa trên signal threshold)
3. Key signal cards
4. Trend bundle (reuse TrendBundle component)
5. Alarm/event timeline placeholder
6. Context panel: hiển thị khi select object trong canvas
```

**Acceptance:**
- FILTER-101, HSP-101 hiển thị condition score + trends
- Context panel hiển thị KHI click object (không phải luôn hiện)
- Trend bundle dùng lại component hiện có

### Phase 6-PV-05 — Config-Driven (2-3h)

```
1. Tạo TypeScript type cho ProcessViewConfig
2. Tách WTP workflow config ra file riêng (wtp-workflow.ts)
3. Loader function: config → components
4. Chuẩn bị JSON schema cho process_view_config (tương lai Contract Registry)
```

**Acceptance:**
- WTP workflow không còn hardcode trong component
- Có thể đổi config để thêm/xóa/sắp xếp process blocks
- Schema sẵn sàng cho Contract Registry integration

### Phase 6-PV-06 — Future Analytics Ready (1-2h, placeholder)

```
1. ImpactPathView placeholder component
2. Relationship config stub
3. Analytics badge placeholder
```

**Acceptance:**
- Placeholder hiển thị "Coming Soon"
- Không block các phase trước

---

## 8. Backward Compatibility

| Cũ | Mới | Cách xử lý |
|----|-----|-----------|
| `/diagrams` route | `/operations` | Redirect 301 |
| `DiagramPage.tsx` | `ProcessViewWorkspace.tsx` | Keep old file, add deprecation comment |
| Sidebar "Diagrams" | "Operations" | Đổi label, giữ icon tạm thời |
| SVG binding YAML | Config-driven views | Giữ YAML parser cho P&ID view, thêm config mới cho workflow |

---

## 9. Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| WTP area hierarchy không khớp workflow blocks | Block drill-down không map được | Dùng area_id mapping table tạm |
| Signal KPI không có sẵn cho tất cả process block | Block hiển thị "—" | Dùng signal mặc định, fallback trống |
| Condition score không có logic thực | Score là simulated | Ghi rõ "Demo" mode |
| Hardcode config quá nhiều | Khó mở rộng plant khác | Tách config ra file riêng từ UI-D2 |
| Asset/signal API chậm khi load nhiều block | UI-D2 chậm | Dùng React Query staleTime + batch current values |

---

## 10. SA Decisions (2026-07-07)

| # | Question | SA Decision |
|---|----------|-------------|
| 1 | Overlay priority | **P0: Status + Alarm. P1: Data Quality.** Quality/Energy/Condition/Risk/Scenario để sau. |
| 2 | WTP Overview mapping | **7 process blocks.** 9 areas giữ trong underlying model/drilldown. |
| 3 | Condition Score | **Rule-based MVP only.** Transparent formula, not ML/APM. Apply selected demo assets first. |
| 4 | Refresh strategy | **Hybrid.** Auto-refresh default cho overview/area/asset. Manual + pause available. Trend/investigation manual default. |
| 5 | GIS | **Separate module.** Link từ Operations khi có spatial context. |

---

## 11. Summary

| Phase | Effort | Deliverable |
|-------|--------|------------|
| 6-PV-01 | 3-4h | Rename + workspace shell + hierarchy panel |
| 6-PV-02 | 3-4h | WTP workflow block diagram (7 blocks) |
| 6-PV-03 | 2-3h | Filtration Area view |
| 6-PV-04 | 3-4h | Asset Condition View (3-5 assets) |
| 6-PV-05 | 2-3h | Config-driven architecture |
| 6-PV-06 | 1-2h | Analytics placeholder |
| **Total** | **14-20h** | |

**Next step:** SA review → answer open questions → start UI-D1.
