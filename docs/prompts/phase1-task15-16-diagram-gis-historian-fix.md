# Phase 1 — Task 15-16: Diagram + GIS Map + Historian Fix (Gộp)

> **Designer:** DeepSeek V4 Pro | **Date:** 2026-06-30

## Context

Hoàn thiện 3 phần cuối của Phase 1:
1. **Fix Historian connection** — backend gọi `adapter.connect()` trong lifespan
2. **SVG Diagrams** — 2 diagram demo (P&ID Process + One-Line Electrical) với dynamic binding
3. **GIS Map** — Leaflet map với asset markers, zoom/pan, click to detail

## Implementation Checklist

- [ ] MODIFY `backend/app/main.py` — connect historian adapter in lifespan
- [ ] CREATE `examples/diagrams/pid-process.svg` — P&ID diagram SVG
- [ ] CREATE `examples/diagrams/pid-process.binding.yaml` — binding config
- [ ] CREATE `examples/diagrams/one-line-electrical.svg` — One-line diagram SVG
- [ ] CREATE `examples/diagrams/one-line-electrical.binding.yaml` — binding config
- [ ] CREATE `frontend/src/features/visualization/DiagramPage.tsx`
- [ ] CREATE `frontend/src/features/visualization/SvgDiagram.tsx`
- [ ] CREATE `frontend/src/features/visualization/GisMapPage.tsx`
- [ ] MODIFY `frontend/src/routes/index.tsx` — replace placeholders
- [ ] INSTALL `leaflet` + `react-leaflet` + `@types/leaflet`

## Detailed Instructions

### 1. `backend/app/main.py` — Historian Fix

Sửa lifespan để init + connect historian adapter:

```python
"""PlantOS Center Backend — FastAPI Application."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import v1_router
from app.core.config import settings
from app.db import get_engine, dispose_engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle."""
    get_engine()

    # Connect historian adapter if TDengine is available
    try:
        from app.modules.historian.tdengine_adapter import TDengineHistorianAdapter
        import app.modules.measurements.router as mr
        adapter = TDengineHistorianAdapter()
        ok = await adapter.connect()
        if ok:
            mr._historian_instance = adapter
            print(f"Historian connected: TDengine at {settings.TDENGINE_HOST}")
        else:
            print("Historian: TDengine unavailable, using Stub")
    except Exception as e:
        print(f"Historian init skipped: {e}")

    yield

    # Shutdown
    if mr._historian_instance and hasattr(mr._historian_instance, 'close'):
        await mr._historian_instance.close()
    dispose_engine()


app = FastAPI(
    title="PlantOS API",
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(v1_router)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": settings.APP_VERSION}
```

### 2. `examples/diagrams/pid-process.svg` — P&ID Diagram

Tạo SVG đơn giản cho process flow: Tank → Pump → Motor → Valve. Mỗi phần tử có `data-asset-id`. Value labels có `data-signal-name`.

```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 300" width="800" height="300">
  <style>
    text { font-family: monospace; }
    .label { fill: #9ca3af; font-size: 8px; }
    .value { font-size: 10px; font-weight: bold; }
    .equipment-label { fill: #e2e8f0; font-size: 9px; text-anchor: middle; }
  </style>
  <rect width="800" height="300" fill="#0f172a"/>

  <!-- Title -->
  <text x="400" y="20" text-anchor="middle" fill="#e2e8f0" font-size="14" font-weight="bold">P&amp;ID — Process Line 01</text>

  <!-- Flow arrows (static) -->
  <line x1="60" y1="150" x2="120" y2="150" stroke="#475569" stroke-width="2" marker-end="url(#arrow)"/>
  <defs><marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M0,0 L10,5 L0,10 Z" fill="#475569"/></marker></defs>

  <!-- TANK-101 -->
  <g data-asset-id="TANK-101" cursor="pointer">
    <rect x="60" y="80" width="80" height="120" rx="4" fill="#1e293b" stroke="#475569" stroke-width="2" data-binding="state"/>
    <text x="100" y="145" class="equipment-label">T-101</text>
    <text x="100" y="160" class="label">Tank</text>
    <!-- Level value -->
    <text x="100" y="210" class="value" data-asset-id="TANK-101" data-signal-name="tank_level" data-binding="signal_value" fill="#22c55e">--.- %</text>
  </g>

  <!-- Pipe Tank→Pump -->
  <line x1="140" y1="140" x2="180" y2="140" stroke="#475569" stroke-width="3"/>

  <!-- PUMP-101 -->
  <g data-asset-id="PUMP-101" cursor="pointer">
    <circle cx="210" cy="140" r="35" fill="#1e293b" stroke="#475569" stroke-width="2" data-binding="state"/>
    <text x="210" y="137" class="equipment-label">P-101</text>
    <text x="210" y="150" class="label">Pump</text>
    <!-- Pressure value -->
    <text x="210" y="185" class="value" data-asset-id="PUMP-101" data-signal-name="discharge_pressure" data-binding="signal_value" fill="#22c55e">--.- bar</text>
  </g>

  <!-- Pipe Pump→Motor -->
  <line x1="245" y1="140" x2="290" y2="140" stroke="#475569" stroke-width="3"/>

  <!-- MOTOR-101 -->
  <g data-asset-id="MOTOR-101" cursor="pointer">
    <circle cx="325" cy="140" r="35" fill="#1e293b" stroke="#475569" stroke-width="2" data-binding="state"/>
    <text x="325" y="137" class="equipment-label">M-101</text>
    <text x="325" y="150" class="label">Motor</text>
    <!-- Current value -->
    <text x="325" y="185" class="value" data-asset-id="MOTOR-101" data-signal-name="motor_current" data-binding="signal_value" fill="#22c55e">--.- A</text>
  </g>

  <!-- Pipe Motor→Valve -->
  <line x1="360" y1="140" x2="420" y2="140" stroke="#475569" stroke-width="3"/>

  <!-- VALVE-101 -->
  <g data-asset-id="VALVE-101" cursor="pointer">
    <polygon points="420,120 440,110 460,120 460,160 440,170 420,160" fill="#1e293b" stroke="#475569" stroke-width="2" data-binding="state"/>
    <text x="440" y="145" class="equipment-label">V-101</text>
    <text x="440" y="158" class="label">Valve</text>
    <text x="440" y="185" class="value" data-asset-id="VALVE-101" data-signal-name="valve_position" data-binding="signal_value" fill="#22c55e">--.- %</text>
  </g>

  <!-- Pipe out -->
  <line x1="460" y1="140" x2="500" y2="140" stroke="#475569" stroke-width="3"/>

  <!-- Legend -->
  <text x="600" y="80" fill="#9ca3af" font-size="9">Legend:</text>
  <circle cx="610" cy="100" r="6" fill="#22c55e"/><text x="622" y="104" fill="#9ca3af" font-size="8">Running</text>
  <circle cx="610" cy="118" r="6" fill="#ef4444"/><text x="622" y="122" fill="#9ca3af" font-size="8">Alarm</text>
  <circle cx="610" cy="136" r="6" fill="#6b7280"/><text x="622" y="140" fill="#9ca3af" font-size="8">Stopped</text>
</svg>
```

### 3. `examples/diagrams/pid-process.binding.yaml`

```yaml
diagram_id: pid-process
diagram_name: P&ID Process Line 01
svg_file: pid-process.svg
refresh_interval_ms: 3000

state_styles:
  running: { stroke: "#22c55e", fill: "#166534" }
  stopped: { stroke: "#6b7280", fill: "#1e293b" }
  warning: { stroke: "#f59e0b", fill: "#78350f" }
  alarm: { stroke: "#ef4444", fill: "#7f1d1d" }
  default: { stroke: "#475569", fill: "#1e293b" }

signals:
  - asset_id: TANK-101
    signal_name: tank_level
    format: "0.0"
    unit: "%"
  - asset_id: PUMP-101
    signal_name: discharge_pressure
    format: "0.0"
    unit: bar
  - asset_id: MOTOR-101
    signal_name: motor_current
    format: "0.0"
    unit: A
  - asset_id: VALVE-101
    signal_name: valve_position
    format: "0.0"
    unit: "%"

states:
  - asset_id: TANK-101
  - asset_id: PUMP-101
  - asset_id: MOTOR-101
  - asset_id: VALVE-101
```

### 4. `examples/diagrams/one-line-electrical.svg` + `one-line-electrical.binding.yaml`

Tương tự P&ID, vẽ sơ đồ điện: Transformer → Feeder → Breaker. Assets: TRANSFORMER-01, FEEDER-01, BREAKER-01. Signals: temperature, current, power, voltage, breaker_status.

> Coder tự thiết kế SVG và YAML theo pattern trên. SVG nên có style tương tự: nền tối, stroke xám, giá trị màu xanh lá.

### 5. `frontend/src/features/visualization/SvgDiagram.tsx`

Component nhận SVG + binding config, fetch current values, update SVG dynamically.

```tsx
import { useEffect, useRef } from "react";
import { useQuery } from "@tanstack/react-query";
import { getCurrentValues } from "@/lib/api";

type Props = { svgUrl: string; binding: any };

export function SvgDiagram({ svgUrl, binding }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);

  // Collect unique asset_ids from binding
  const assetIds = [...new Set(binding.signals?.map((s: any) => s.asset_id) || [])];

  const { data: currentValues } = useQuery({
    queryKey: ["diagram-values", assetIds],
    queryFn: async () => {
      const result: Record<string, any> = {};
      for (const aid of assetIds) {
        try {
          const vals = await getCurrentValues({ asset_id: aid });
          vals?.forEach((v: any) => { result[v.signal_id] = v; });
        } catch {}
      }
      return result;
    },
    refetchInterval: binding.refresh_interval_ms || 5000,
  });

  useEffect(() => {
    if (!containerRef.current || !currentValues) return;
    const container = containerRef.current;

    // Update state styles
    container.querySelectorAll("[data-binding='state']").forEach((el: any) => {
      const assetId = el.closest("[data-asset-id]")?.getAttribute("data-asset-id");
      if (!assetId) return;
      const stateSignal = binding.states?.find((s: any) => s.asset_id === assetId);
      const style = binding.state_styles?.default || {};
      // Apply default state style (MVP: always show default unless we have state signals)
      Object.entries(style).forEach(([k, v]) => { el.setAttribute(k, v as string); });
    });

    // Update signal values
    container.querySelectorAll("[data-binding='signal_value']").forEach((el: any) => {
      const signalName = el.getAttribute("data-signal-name");
      const assetId = el.getAttribute("data-asset-id");
      if (!signalName) return;
      const key = `${assetId}.${signalName}`;
      const cv = currentValues[key];
      const sigConfig = binding.signals?.find((s: any) => s.signal_name === signalName && s.asset_id === assetId);

      if (cv && cv.value !== null && cv.value !== undefined) {
        const fmt = sigConfig?.format || "0.0";
        const unit = sigConfig?.unit || "";
        let display = typeof cv.value === "number" ? cv.value.toFixed(fmt.includes(".") ? fmt.split(".")[1].length : 1) : cv.value;
        el.textContent = `${display} ${unit}`;
        el.setAttribute("fill", cv.quality === "GOOD" ? "#22c55e" : "#ef4444");
      }
    });
  }, [currentValues, binding]);

  return (
    <div ref={containerRef} className="flex justify-center overflow-auto" dangerouslySetInnerHTML={{ __html: "" }} />
  );
}
```

> **Quan trọng:** Cách tiếp cận trên dùng `dangerouslySetInnerHTML` cho SVG inline. **Coder nên dùng fetch SVG file** thay vì hardcode SVG trong React. Fetch SVG text → parse → inject vào container. Cập nhật DOM elements bằng DOM API thay vì React re-render cho performance.

Coder tự điều chỉnh implementation — pattern chính: fetch SVG file → set innerHTML → querySelector update values.

### 6. `frontend/src/features/visualization/DiagramPage.tsx`

Dropdown chọn diagram, load SVG + binding config.

```tsx
import { useState } from "react";
import { SvgDiagram } from "./SvgDiagram";

const DIAGRAMS = [
  { id: "pid-process", name: "P&ID Process Line 01", svg: "/diagrams/pid-process.svg", binding: null },
  { id: "one-line-electrical", name: "One-Line Electrical", svg: "/diagrams/one-line-electrical.svg", binding: null },
];

// Import binding YAML as JSON (Coder: fetch from /diagrams/*.binding.yaml or inline as object)
import pidBinding from "../../../examples/diagrams/pid-process.binding.yaml?raw";
// Note: Vite can import YAML with @rollup/plugin-yaml or parse manually

export function DiagramPage() {
  const [diagramId, setDiagramId] = useState("pid-process");
  const diagram = DIAGRAMS.find(d => d.id === diagramId) || DIAGRAMS[0];

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Diagrams</h1>
        <select value={diagramId} onChange={e => setDiagramId(e.target.value)}
          className="bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm">
          {DIAGRAMS.map(d => <option key={d.id} value={d.id}>{d.name}</option>)}
        </select>
      </div>
      <div className="bg-gray-900/50 rounded-lg border border-gray-800 p-4">
        <SvgDiagram svgUrl={diagram.svg} binding={{}} />
      </div>
    </div>
  );
}
```

> **Coder:** Cần resolve cách load SVG + YAML binding trong Vite. Có 2 cách:
> 1. Copy SVG vào `frontend/public/diagrams/` → fetch bằng `/diagrams/pid-process.svg`
> 2. Import SVG as raw string: `import pidSvg from "...svg?raw"`
> Chọn cách đơn giản nhất hoạt động.

### 7. `frontend/src/features/visualization/GisMapPage.tsx`

Leaflet map với asset markers.

```tsx
import { useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { getAssets, getCurrentValues } from "@/lib/api";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

// Fix default marker icon (Leaflet + Vite issue)
import markerIcon2x from "leaflet/dist/images/marker-icon-2x.png";
import markerIcon from "leaflet/dist/images/marker-icon.png";
import markerShadow from "leaflet/dist/images/marker-shadow.png";
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({ iconRetinaUrl: markerIcon2x, iconUrl: markerIcon, shadowUrl: markerShadow });

function createColoredIcon(color: string) {
  return L.divIcon({
    className: "",
    html: `<div style="width:14px;height:14px;border-radius:50%;background:${color};border:2px solid white;box-shadow:0 0 4px rgba(0,0,0,0.5)"></div>`,
    iconSize: [14, 14],
    iconAnchor: [7, 7],
  });
}

const statusColor: Record<string, string> = { active: "#22c55e", running: "#3b82f6", warning: "#f59e0b", alarm: "#ef4444" };

export function GisMapPage() {
  const { data: assets } = useQuery({ queryKey: ["assets"], queryFn: () => getAssets() });
  const { data: currentValues } = useQuery({
    queryKey: ["all-current"],
    queryFn: async () => {
      const all = await getCurrentValues({ asset_id: "PUMP-101" }); // MVP: fetch per asset
      return all;
    },
    refetchInterval: 10000,
  });

  useEffect(() => {
    const map = L.map("gis-map").setView([10.7626, 106.6602], 16);
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution: "&copy; OpenStreetMap",
      maxZoom: 19,
    }).addTo(map);

    assets?.forEach((a: any) => {
      if (a.location?.lat && a.location?.lng) {
        const marker = L.marker([a.location.lat, a.location.lng], {
          icon: createColoredIcon(statusColor[a.lifecycle_status] || "#6b7280"),
        }).addTo(map);

        marker.bindPopup(`<b>${a.name}</b><br/>${a.asset_id}<br/>${a.lifecycle_status}`);
        marker.on("click", () => {
          window.location.href = `/assets/${a.asset_id}`;
        });
      }
    });

    return () => { map.remove(); };
  }, [assets]);

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">GIS Map</h1>
      <div className="text-sm text-gray-500">{assets?.filter((a: any) => a.location).length || 0} assets with location</div>
      <div id="gis-map" className="h-[500px] rounded-lg border border-gray-800" />
    </div>
  );
}
```

### 8. Update Routes

```tsx
import { DiagramPage } from "@/features/visualization/DiagramPage";
import { GisMapPage } from "@/features/visualization/GisMapPage";

{ path: "diagrams", element: <DiagramPage /> },
{ path: "gis", element: <GisMapPage /> },
```

### 9. Install

```bash
cd frontend
npm install leaflet react-leaflet @types/leaflet
```

### 10. Copy SVG + Binding to `frontend/public/diagrams/`

Copy `examples/diagrams/*.svg` và `*.binding.yaml` vào `frontend/public/diagrams/` để frontend có thể fetch.

## Constraints

- [x] Diagram binding theo `data-asset-id` + `data-signal-name` — không raw tag
- [x] GIS marker click → navigate asset detail
- [x] GIS dùng OpenStreetMap tiles (free, no API key)
- [x] SVG state màu theo design tokens
- [x] Historian fix: connect trong lifespan, fallback Stub nếu fail

## Validation

```bash
# Restart backend (historian fix)
# Start simulator 15s for data
python d:\Project\Github\PlantOS\edge\simulator\simulator.py --config d:\Project\Github\PlantOS\examples\demo-plant\demo-plant.yaml --duration 15

# Open Diagrams page → verify SVG renders with dynamic values
open http://localhost:5173/diagrams

# Open GIS Map → verify marker at PUMP-101 location
open http://localhost:5173/gis
```
