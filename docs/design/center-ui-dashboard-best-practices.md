# PlantOS Center UI — Dashboard Best Practices Integration

**Date:** 2026-07-03 | **Reference:** justinmind.com/dashboard-design-best-practices-ux

---

## Key Insights Added to Plan

### 1. Dashboard Type Confirmation

Bài viết phân loại 3 kiểu dashboard: **Operational, Analytical, Strategic**.

```
Operational → "what's happening right now" → PlantOS ✅
Analytical → "trends and problems" → PlantOS Historian
Strategic → "KPIs vs goals" → PlantOS Management view
```

PlantOS là **Operational Dashboard** là chính. Điều này khẳng định chọn **Alternative A** làm default.

### 2. "5-6 Cards" Rule — Cập nhật Layout

Bài viết nhấn mạnh: **"The best dashboards tend not to include more than 5 or 6 cards in their initial view."**

Layout hiện tại trong plan có ~8 elements. Cần rút gọn Overview:

```
TRƯỚC (8 elements):
  KPI row (5 cards) + Workflow diagram + Incidents panel + 2 trend panels

SAU (5-6 elements, single screen):
  KPI row (4 cards) + Workflow diagram + Mini trend + Alarm badge
  → Drill-down cho detail
```

### 3. F-Pattern Reading — Ưu tiên Top-Left

Bài viết: **"Structure so the most important data is visible at top left."**

Điều chỉnh thứ tự KPI cards:

```
┌──────────────────┬──────────┬──────────┬──────────┐
│ Plant Health     │ Alarms   │ Quality  │ Cost/m³  │  ← Quan trọng nhất bên trái
│ (most critical)  │          │          │          │
└──────────────────┴──────────┴──────────┴──────────┘
```

### 4. "Lead with Key Data" — Big Bold Numbers

Bài viết: **"Great dashboards lead with key data... big, bold numbers."**

KPI card thiết kế:

```
┌─────────────┐
│ Plant Health │
│             │
│    ✅        │  ← Icon trạng thái (không chỉ text)
│   Normal    │  ← Label
│             │
│ 3 areas OK  │  ← Context detail
│ 1 warning   │
└─────────────┘
```

Font size KPI value: **28-36px**, đủ lớn để đọc từ xa.

### 5. Single Screen — Không scroll

Bài viết: **"Stick to a single screen to improve dashboard UX."**

Ràng buộc mới: Overview page **phải fit 1 màn hình** (1920x1080), không scroll. Mọi detail qua drill-down.

### 6. Grid Layout + Visual Hierarchy

Bài viết: **"Think of a grid system as the invisible scaffolding."**

Dùng CSS Grid 12-column cho toàn bộ layout card. Mỗi card có `col-span` xác định:

```
Row 1: [Health: span 3] [Alarms: span 3] [Quality: span 3] [Cost: span 3]
Row 2: [Workflow: span 8] [Incidents: span 4]
Row 3: [Trend snapshot: span 12]
```

### 7. White Space

Bài viết: **"Balance metrics with suitable white space to create breathing room."**

Thêm `gap-4` hoặc `gap-6` giữa các card. Không nhồi nhét.

---

## Cập nhật PM Decision

| Mục | Trước | Sau (có thêm insight) |
|-----|-------|----------------------|
| Cards trên Overview | ~8 | **5-6 max** |
| KPI card order | Bất kỳ | **Top-left = quan trọng nhất** |
| KPI value size | 24px | **28-36px** |
| Scroll trên Overview | Cho phép | **Single screen, no scroll** |
| Layout engine | Flex | **CSS Grid 12-column** |
| Card spacing | `gap-2` | **`gap-4` minimum** |

---

## Không thay đổi

Các quyết định cốt lõi vẫn giữ nguyên:

- ✅ Alt A — Operations Cockpit là default
- ✅ Dark-first, token-ready
- ✅ Lucide icons
- ✅ Phase R1 → R2 → R3 → R4
- ✅ 2 diagram styles: workflow + simplified P&ID
- ✅ 3 workspace: Operations, Management, Data Foundation
