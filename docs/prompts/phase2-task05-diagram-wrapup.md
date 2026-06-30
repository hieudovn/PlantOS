# Phase 2 — Task 2-05: Diagram Enhancement + Phase 2 Wrap-Up

> **Designer:** DeepSeek V4 Pro | **Date:** 2026-06-30
> **Final task of Phase 2!**

## Context

Hoàn thiện diagram với click→detail, state-driven màu, tooltip hover. Wrap-up Phase 2.

## Implementation Checklist

- [ ] MODIFY `frontend/src/features/visualization/SvgDiagram.tsx` — click, hover, state colors
- [ ] UPDATE `README.md` — Phase 2 features
- [ ] RUN `python -m pytest tests/ -v` — verify 44 tests

## Detailed Instructions

### 1. `SvgDiagram.tsx` — Click + Hover + State Colors

Thêm vào useEffect xử lý SVG DOM:

```tsx
// ---- Click handler: navigate to asset detail ----
container.querySelectorAll("[data-asset-id]").forEach((el: any) => {
  const assetId = el.getAttribute("data-asset-id");
  if (!assetId || el._clickBound) return;
  el._clickBound = true;
  el.style.cursor = "pointer";
  el.addEventListener("click", () => {
    window.location.href = `/assets/${assetId}`;
  });
});

// ---- Hover handler: tooltip ----
container.querySelectorAll("[data-asset-id]").forEach((el: any) => {
  if (el._hoverBound) return;
  el._hoverBound = true;
  const assetId = el.getAttribute("data-asset-id");

  el.addEventListener("mouseenter", (e: MouseEvent) => {
    const tooltip = document.createElement("div");
    tooltip.className = "fixed z-50 bg-gray-800 border border-gray-600 rounded px-3 py-2 text-xs shadow-lg pointer-events-none";
    tooltip.style.left = `${e.clientX + 12}px`;
    tooltip.style.top = `${e.clientY - 8}px`;
    tooltip.id = "svg-tooltip";

    // Show asset name + status
    const name = el.querySelector(".equipment-label")?.textContent || assetId;
    tooltip.innerHTML = `<div class="font-medium">${name}</div><div class="text-gray-400">${assetId}</div>`;
    document.body.appendChild(tooltip);

    el.addEventListener("mousemove", (ev: MouseEvent) => {
      const tip = document.getElementById("svg-tooltip");
      if (tip) { tip.style.left = `${ev.clientX + 12}px`; tip.style.top = `${ev.clientY - 8}px`; }
    });
  });

  el.addEventListener("mouseleave", () => {
    const tip = document.getElementById("svg-tooltip");
    if (tip) tip.remove();
  });
});

// ---- State-driven colors from current values ----
container.querySelectorAll("[data-binding='state']").forEach((el: any) => {
  const g = el.closest("[data-asset-id]") as HTMLElement;
  const assetId = g?.getAttribute("data-asset-id");
  if (!assetId) return;

  // Find a "status" signal for this asset (running_status, breaker_status, etc.)
  let stateValue: string | null = null;
  for (const [key, cv] of Object.entries(currentValues)) {
    if (key.startsWith(assetId) && (key.includes("status") || key.includes("running"))) {
      stateValue = cv?.value ? "running" : "stopped";
      break;
    }
  }

  // Default to active if no status signal found
  if (stateValue === null) stateValue = "running";

  const styles = binding.state_styles || {};
  const stateStyle = styles[stateValue] || styles.default || { stroke: "#475569", fill: "#1e293b" };
  Object.entries(stateStyle).forEach(([k, v]) => {
    el.setAttribute(k, v as string);
  });
});
```

### 2. `README.md` — Add Phase 2 Features

```markdown
## Phase 2 Features

- **Edge Agent** — DuckDB local buffer, MQTT publisher, store-and-forward sync
- **Edge Fleet UI** — Real-time node status, heartbeat monitoring
- **Asset Tree View** — UNS hierarchy navigation (Plant → Area → Asset)
- **WebSocket Real-time** — Live data push for Asset Detail + Diagrams
- **UX Polish** — Chart state persistence, tab rename, chart type selector
- **Diagram Enhancement** — Click element → asset detail, state-driven colors, hover tooltip
```

### 3. Test Suite

```bash
cd backend && python -m pytest tests/ -v
# Expected: 44 passed
```

## Files

| # | File | Action |
|---|------|--------|
| 1 | `frontend/src/features/visualization/SvgDiagram.tsx` | MODIFY |
| 2 | `README.md` | MODIFY |

## Validation

```bash
# 1. Open P&ID diagram, click pump symbol → navigate to /assets/PUMP-101
# 2. Hover any equipment → tooltip with name + asset_id
# 3. Verify state colors: running=green stroke, stopped=gray
```
