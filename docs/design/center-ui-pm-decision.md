# PlantOS Center UI/UX — PM Decision & Implementation Plan

**Date:** 2026-07-03 | **PM:** V4 Pro Designer-Planner

---

## 1. Đánh giá 3 Phương Án

### Alternative A — Industrial Operations Cockpit

| Tiêu chí | Điểm | Nhận xét |
|----------|------|----------|
| Phù hợp operator | ⭐⭐⭐⭐⭐ | Thiết kế cho control room, dark-first, status-heavy |
| Phù hợp maintenance | ⭐⭐⭐⭐ | Asset health, trend, alarm context |
| Phù hợp management | ⭐⭐ | Quá technical, cần thêm light/report view |
| Phù hợp data/engineering | ⭐⭐⭐ | Có drill-down nhưng chưa đủ admin tools |
| Demo/presales impact | ⭐⭐⭐⭐⭐ | Ấn tượng mạnh, phù hợp WTP reference |
| Rủi ro SCADA clone | ⚠️ Medium | Cần governance chặt về diagram style |
| Độ phức tạp implement | Medium | Cần workflow diagram engine + KPI cards |

**Kết luận:** Phù hợp nhất làm **default landing page**.

### Alternative B — Hybrid Management & Operations

| Tiêu chí | Điểm | Nhận xét |
|----------|------|----------|
| Phù hợp operator | ⭐⭐ | Quá summarized, thiếu realtime feel |
| Phù hợp management | ⭐⭐⭐⭐⭐ | Report-friendly, light mode, export |
| Phù hợp data/engineering | ⭐⭐ | Không đủ technical depth |
| Rủi ro Grafana clone | ⚠️ Low-Medium | Có thể giống dashboard tool nếu không cẩn thận |

**Kết luận:** Nên làm **Management/Reports workspace riêng**, không phải default.

### Alternative C — Data Foundation & Asset Intelligence

| Tiêu chí | Điểm | Nhận xét |
|----------|------|----------|
| Phù hợp operator | ⭐ | Quá technical |
| Phù hợp data/engineering | ⭐⭐⭐⭐⭐ | Asset tree, UNS, lineage, source health |
| Rủi ro admin console | ⚠️ High | Dễ thành technical tool nếu làm default |

**Kết luận:** Nên làm **Data Foundation workspace riêng**, không phải default.

---

## 2. Quyết Định PM — Chiến Lược 3 Workspace

```
┌─────────────────────────────────────────────────────────┐
│                 PLANTOS CENTER                           │
│                                                         │
│  ┌─────────────────┐  ┌──────────────┐  ┌────────────┐ │
│  │ OPERATIONS       │  │ MANAGEMENT   │  │ DATA       │ │
│  │ (Default home)   │  │ (Reports)    │  │ FOUNDATION │ │
│  │                  │  │              │  │            │ │
│  │ Alt A: Cockpit   │  │ Alt B: Mgmt  │  │ Alt C: DF  │ │
│  │ Dark-first       │  │ Light-ready  │  │ Dark/light │ │
│  │ Operator-focused │  │ Report-ready │  │ Technical  │ │
│  └─────────────────┘  └──────────────┘  └────────────┘ │
└─────────────────────────────────────────────────────────┘
```

**Default:** Operations Cockpit (Alt A)  
**Phase 1:** Chỉ làm Operations view  
**Phase 2:** Thêm Management  
**Phase 3:** Thêm Data Foundation

---

## 3. Information Architecture — Đề Xuất

```
Sidebar Navigation
├── 📊 Overview              ← Alt A: Plant health + KPI + workflow diagram
├── 🏗️ Operations            ← Alt A: Area cockpit + P&ID diagram
│   ├── Process Flow         ← Workflow diagram (default)
│   └── P&ID Detail          ← Simplified P&ID (drill-down)
├── ⚙️ Assets                ← Asset registry + health + tree
├── 📈 Trends                ← Historian + trend bundles
├── 🚨 Alarms                ← Active + history + timeline
├── 🧠 Intelligence          ← Traceability + Energy/Cost + Root Cause
├── ─────────────────
├── 📊 Management            ← Alt B: Summary + Reports (Phase 2)
├── 🗄️ Data Foundation       ← Alt C: Signals + UNS + Bindings (Phase 3)
├── 🖥️ Edge & Sources        ← Edge Fleet + Source Health
├── ⚡ System                ← DB stats + Server (hidden from default)
├── ─────────────────
└── ⚙️ Settings
```

---

## 4. Layout — Center Landing Page (Operations Cockpit)

```
┌──────────────────────────────────────────────────────────────┐
│ TOPBAR: [Plant ▾] | Data: ● Live | 🔔 3 Alarms | 👤 User    │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────┬──────────┬──────────┬──────────┬──────────┐    │
│  │ Health  │ Product. │ Quality  │ Energy   │ Cost/m³  │    │
│  │ ✅ Good │ 8,450 m³ │ 98.2%    │ 0.38     │ 3,200    │    │
│  │         │ ▲ 2.1%   │ compliant│ kWh/m³   │ VND/m³   │    │
│  └─────────┴──────────┴──────────┴──────────┴──────────┘    │
│                                                              │
│  ┌────────────────────────────────────┬───────────────────┐  │
│  │ WORKFLOW DIAGRAM                   │ ACTIVE INCIDENTS  │  │
│  │                                    │                   │  │
│  │ [Intake] → [Dosing] → [Clarifier]  │ ● Filter DP High  │  │
│  │    ✅         ✅          ✅        │   High · 10:30    │  │
│  │     ↓           ↓          ↓       │                   │  │
│  │ [Filter] → [Disinfect] → [Outlet]  │ ● Turbidity Warn  │  │
│  │    ✅          ✅           ✅      │   Medium · 10:15  │  │
│  │                                    │                   │  │
│  └────────────────────────────────────┴───────────────────┘  │
│                                                              │
│  ┌──────────────────────┬──────────────────────────────────┐ │
│  │ QUALITY TREND        │ ENERGY & COST TREND              │ │
│  │ (turbidity chain)    │ (kWh/m³ + VND/m³)               │ │
│  └──────────────────────┴──────────────────────────────────┘ │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## 5. Quy Tắc Giao Diện

### 5.1 Màu sắc — Semantic Tokens

```css
/* Không hardcode màu trong component — dùng token */
:root {
  --surface-primary: #0f172a;    /* nền chính */
  --surface-card: #1e293b;       /* card */
  --surface-hover: #334155;      /* hover */
  --border-default: #334155;     /* viền */
  --text-primary: #f1f5f9;       /* chữ chính */
  --text-secondary: #94a3b8;     /* chữ phụ */
  --text-muted: #64748b;         /* chữ mờ */

  /* Status — nhất quán toàn app */
  --status-normal: #22c55e;      /* green */
  --status-warning: #eab308;     /* amber */
  --status-critical: #ef4444;    /* red */
  --status-offline: #6b7280;     /* gray */
  --status-simulated: #a855f7;   /* purple */

  /* Data quality */
  --quality-good: #22c55e;
  --quality-uncertain: #eab308;
  --quality-bad: #ef4444;
  --quality-stale: #6b7280;

  /* Accent */
  --accent: #3b82f6;             /* blue */
}
```

### 5.2 Dark/Light Mode

- **Dark-first**: Mặc định cho Operations view
- **Theme-ready**: Tất cả component dùng token, không hardcode `bg-gray-900`
- **Light mode**: Kích hoạt sau khi có token system, ưu tiên cho Management view

### 5.3 Icon

- Dùng **Lucide icons** (line-based, consistent stroke)
- KHÔNG dùng emoji trong production
- Mỗi icon có 1 ý nghĩa duy nhất

### 5.4 Typography

- **UI font**: Inter (chính), IBM Plex Sans (fallback)
- **Mono font**: JetBrains Mono (cho asset_id, signal_id, UNS path, timestamp)
- **Scale**: Title 24px, Section 16px, Card label 13px, KPI value 28px, Table 13px, Meta 11px

### 5.5 KPI Card

Mỗi card phải có:
```
Label | Value + Unit | Trend indicator | Data quality dot | Last update
```

### 5.6 Bảng

Mọi bảng phải hỗ trợ: Search, Filter, Sort, Row click → detail

### 5.7 Trend Chart

- Line chart mặc định
- Trend bundles (pre-configured), không bắt user pick raw signal
- Hiển thị threshold bands, alarm markers nếu có

### 5.8 Alarm Widget

- Badge: severity color + icon + count
- List: time, severity, asset, signal, description, acknowledged
- Lifecycle: Active → Acknowledged → Resolved

---

## 6. Diagram Strategy

### 6.1 Hai kiểu diagram

| Style | Target User | Hiển thị |
|-------|------------|----------|
| **Workflow / Production Units** | Operator, Manager, Cross-functional | Block diagram, status color, 1-2 KPI per block |
| **Simplified P&ID** | Engineer, Maintenance, Technical | Equipment icons, pipes, measurement points, live values |

### 6.2 Workflow Diagram — Dùng React Flow

```
[Intake] → [Chemical Dosing] → [Clarification] → [Filtration] → [Disinfection] → [Distribution]
   ✅           ✅                 ✅                ✅              ✅               ✅
  85 NTU      12 L/min          5.2 NTU          0.3 NTU        0.6 mg/L        0.25 NTU
```

### 6.3 Simplified P&ID — Dùng SVG runtime (hiện có)

Giữ nguyên cơ chế SVG + binding YAML, chỉ cải thiện visual.

---

## 7. Component Architecture

```
src/components/
├── layout/
│   ├── Sidebar.tsx           ← grouped navigation
│   ├── Topbar.tsx            ← plant selector + status + user
│   └── Shell.tsx             ← layout wrapper
├── ui/                       ← shadcn/ui primitives
│   ├── Card.tsx, Badge.tsx, Table.tsx, Tabs.tsx, Dialog.tsx
├── industrial/               ← PlantOS-specific widgets
│   ├── KpiCard.tsx           ← value + unit + trend + quality
│   ├── StatusBadge.tsx       ← existing, enhance
│   ├── DataQualityBadge.tsx  ← freshness + quality dot
│   ├── AlarmBadge.tsx        ← severity + count
│   ├── AssetHealthBar.tsx    ← color-coded summary
│   └── TrendBundle.tsx       ← pre-configured multi-signal chart
├── charts/
│   └── TrendChart.tsx        ← existing, refactor with tokens
├── diagrams/
│   ├── WorkflowDiagram.tsx   ← React Flow block diagram
│   └── SvgDiagram.tsx        ← existing P&ID viewer
└── data-foundation/          ← Phase 3
    ├── AssetTree.tsx, SignalTable.tsx, UnsPath.tsx, BindingCard.tsx
```

---

## 8. Implementation Plan — 4 Phases

### Phase R1: Foundation (1 tuần) — Rủi ro: Thấp

| Task | Mô tả |
|------|-------|
| R1.1 | Tạo `tokens.css` với CSS variables |
| R1.2 | Thay emoji → Lucide icons trong Sidebar |
| R1.3 | Thêm `DataQualityBadge` component |
| R1.4 | Thay "MVP Preview" → version badge |
| R1.5 | Refactor Topbar/Sidebar dùng tokens |

**Không đụng:** Route, API, page content, diagram, historian, asset table.

### Phase R2: Operations Cockpit (2 tuần) — Rủi ro: Medium

| Task | Mô tả |
|------|-------|
| R2.1 | Tạo `KpiCard` component |
| R2.2 | Tạo `WorkflowDiagram` component (React Flow) |
| R2.3 | Redesign Overview page theo Alt A layout |
| R2.4 | Thêm AlarmBadge vào Topbar |
| R2.5 | Tạo Operations page với workflow diagram |

**Giữ song song:** Overview cũ (đổi tên "System") và Overview mới.

### Phase R3: Navigation + Components (1 tuần)

| Task | Mô tả |
|------|-------|
| R3.1 | Reorganize sidebar theo IA mới |
| R3.2 | Tạo `TrendBundle` component |
| R3.3 | Cải thiện Alarm page với timeline view |

### Phase R4: Management + Data Foundation (2 tuần)

| Task | Mô tả |
|------|-------|
| R4.1 | Tạo Management Summary page (Alt B) |
| R4.2 | Tạo Data Foundation page (Alt C) |
| R4.3 | Light theme readiness |

---

## 9. Phase R1 Scope — Chi Tiết

**Chỉ làm Phase R1 ngay.** Đây là 5 task nhỏ, an toàn, không phá gì:

### R1.1 — `tokens.css`

Tạo file `frontend/src/styles/tokens.css` với semantic variables. Import vào `globals.css`.

### R1.2 — Icon Replacement

| Current | Replace |
|---------|---------|
| 🏭 | `LayoutDashboard` |
| 📋 | `Boxes` |
| 📡 | `Activity` |
| 📈 | `LineChart` |
| 🗺️ | `Workflow` |
| 🌍 | `MapPin` |
| 🚨 | `Bell` |
| 🖥️ | `Server` |

### R1.3 — DataQualityBadge

```tsx
<DataQualityBadge quality="GOOD" timestamp="2026-07-03T10:30:00Z" />
// → 🟢 Good · 3s ago
```

### R1.4 — Version Badge

Thay text "MVP Preview" → `v0.1.0` badge nhỏ.

### R1.5 — Topbar/Sidebar Token Refactor

Thay `bg-gray-900` → `var(--surface-primary)`, etc.

---

## 10. Rủi Ro & Mitigation

| Rủi ro | Mức độ | Mitigation |
|--------|--------|------------|
| UI giống SCADA | Medium | Không thêm control, diagram read-only, workflow-first |
| UI giống Grafana | Low | Không dashboard builder, tập trung context |
| UI quá technical | Medium | Alt A làm default, Alt C ẩn trong Data Foundation |
| Hardcode WTP | High | Dùng config/contract, không hardcode plant ID trong component |
| Thiếu theme token | **Critical (hiện tại)** | R1.1 fix ngay |
| Thiếu data freshness | Medium | R1.3 DataQualityBadge |
| Phá route hiện có | Low | Giữ nguyên tất cả route, thêm mới thay vì sửa |

---

## 11. Rollback Plan

- Mỗi phase có branch riêng
- Overview cũ rename → "System", không xóa
- Tokens dùng CSS variables với fallback
- Nếu React Flow lỗi → fallback về SVG diagram cũ

---

## 12. Quyết Định PM — Tổng Kết

| Câu hỏi | Quyết định |
|---------|-----------|
| Default landing page? | **Alt A — Operations Cockpit** |
| Management view? | Alt B — workspace riêng (Phase 4) |
| Data Foundation? | Alt C — workspace riêng (Phase 4) |
| Dark/Light? | Dark-first, token-ready cho light |
| Diagram đầu tiên? | Workflow block diagram (React Flow) |
| P&ID? | Giữ SVG runtime hiện có, cải thiện visual |
| Phase đầu tiên? | **R1: Foundation** — 5 task, an toàn |
| Có code ngay không? | Chưa — cần approval trước |
