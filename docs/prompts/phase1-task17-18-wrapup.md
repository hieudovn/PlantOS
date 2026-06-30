# Phase 1 — Task 17-18: README + MVP Validation + Final Fixes (Wrap-Up)

> **Designer:** DeepSeek V4 Pro | **Date:** 2026-06-30
> **Final task of Phase 1!**

## Context

Hoàn thiện Phase 1: fix historian data flow, thêm zoom/pan cho diagram, cập nhật README, chạy test suite, kiểm tra MVP acceptance criteria.

## Implementation Checklist

- [ ] MODIFY `backend/app/modules/measurements/router.py` — fix `get_historian()` async connect
- [ ] ROLLBACK `backend/app/main.py` — remove historian from lifespan (moved to router)
- [ ] MODIFY `frontend/src/features/visualization/SvgDiagram.tsx` — add zoom/pan
- [ ] MODIFY `README.md` — full run instructions
- [ ] RUN `python -m pytest tests/ -v` — verify all 44 tests pass
- [ ] CHECK MVP acceptance criteria (`docs/12-mvp-scope.md` §9)

## Detailed Instructions

### 1. `backend/app/modules/measurements/router.py` — Fix Historian

Thay `get_historian()` sync → async, tự connect TDengine bên trong:

```python
"""Measurement API — FastAPI router."""

from fastapi import APIRouter, HTTPException, Query, Depends

from app.modules.historian.interface import HistorianInterface
from app.modules.historian.stub_adapter import StubHistorianAdapter
from app.modules.measurements.schemas import (
    IngestRequest, IngestResponse, CurrentValueResponse,
    HistoryQueryParams, HistoryResponse,
)
from app.modules.measurements.service import MeasurementService

_historian_instance: HistorianInterface | None = None


async def get_historian() -> HistorianInterface:
    """Async dependency — connect TDengine on first call, cache singleton.

    Tries TDengine first; falls back to Stub if unavailable.
    """
    global _historian_instance
    if _historian_instance is not None:
        return _historian_instance

    try:
        from app.modules.historian.tdengine_adapter import TDengineHistorianAdapter
        adapter = TDengineHistorianAdapter()
        ok = await adapter.connect()
        if ok:
            _historian_instance = adapter
            return adapter
    except Exception:
        pass

    _historian_instance = StubHistorianAdapter()
    return _historian_instance


router = APIRouter()

# ... (rest of routes unchanged, but all use `historian: HistorianInterface = Depends(get_historian)`)
```

> **Quan trọng:** FastAPI hỗ trợ async dependency functions. `Depends(get_historian)` sẽ await đúng cách. Lần đầu request hơi chậm (connect TDengine ~1s), các lần sau instant.

### 2. `backend/app/main.py` — Rollback Historian from Lifespan

Xóa đoạn historian connect trong lifespan. Chỉ giữ engine init + CORS.

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle."""
    get_engine()
    yield
    dispose_engine()
```

### 3. `frontend/src/features/visualization/SvgDiagram.tsx` — Add Zoom/Pan

Thêm zoom (scroll wheel) và pan (drag mouse):

```tsx
import { useEffect, useRef, useState, useCallback } from "react";
import { useQuery } from "@tanstack/react-query";
import { getCurrentValues } from "@/lib/api";

type Props = { svgUrl: string; binding: any };

export function SvgDiagram({ svgUrl, binding }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const svgWrapperRef = useRef<HTMLDivElement>(null);
  const [svgContent, setSvgContent] = useState<string>("");

  // ---- Zoom & Pan state ----
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [dragging, setDragging] = useState(false);
  const dragStart = useRef({ x: 0, y: 0 });

  const handleWheel = useCallback((e: WheelEvent) => {
    e.preventDefault();
    const delta = e.deltaY > 0 ? -0.1 : 0.1;
    setZoom(z => Math.max(0.2, Math.min(5, z + delta)));
  }, []);

  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    if (e.button !== 0) return;
    setDragging(true);
    dragStart.current = { x: e.clientX - pan.x, y: e.clientY - pan.y };
  }, [pan]);

  const handleMouseMove = useCallback((e: React.MouseEvent) => {
    if (!dragging) return;
    setPan({ x: e.clientX - dragStart.current.x, y: e.clientY - dragStart.current.y });
  }, [dragging]);

  const handleMouseUp = useCallback(() => setDragging(false), []);

  // Attach wheel listener to container
  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    el.addEventListener("wheel", handleWheel, { passive: false });
    return () => el.removeEventListener("wheel", handleWheel);
  }, [handleWheel]);

  // ---- SVG Fetch ----
  useEffect(() => {
    fetch(svgUrl)
      .then(r => r.text())
      .then(setSvgContent)
      .catch(() => setSvgContent("<p class='text-red-400 p-4'>Failed to load SVG</p>"));
  }, [svgUrl]);

  // ---- Live Data ----
  const assetIds = [...new Set(binding.signals?.map((s: any) => s.asset_id) || [])];

  const { data: currentValues } = useQuery({
    queryKey: ["diagram-values", assetIds],
    queryFn: async () => {
      const result: Record<string, any> = {};
      for (const aid of assetIds as string[]) {
        try {
          const vals = await getCurrentValues({ asset_id: aid });
          vals?.forEach((v: any) => { result[v.signal_id] = v; });
        } catch { /* ignore */ }
      }
      return result;
    },
    refetchInterval: binding.refresh_interval_ms || 5000,
  });

  useEffect(() => {
    if (!containerRef.current || !currentValues) return;
    const container = containerRef.current;

    container.querySelectorAll("[data-binding='state']").forEach((el: any) => {
      const g = el.closest("[data-asset-id]") as HTMLElement;
      const assetId = g?.getAttribute("data-asset-id");
      if (!assetId) return;
      const style = binding.state_styles?.default || {};
      Object.entries(style).forEach(([k, v]) => { el.setAttribute(k, v as string); });
    });

    container.querySelectorAll("[data-binding='signal_value']").forEach((el: any) => {
      const signalName = el.getAttribute("data-signal-name");
      const assetId = el.getAttribute("data-asset-id");
      if (!signalName) return;
      const key = `${assetId}.${signalName}`;
      const cv = currentValues[key];
      const sigConfig = binding.signals?.find(
        (s: any) => s.signal_name === signalName && s.asset_id === assetId
      );
      if (cv && cv.value !== null && cv.value !== undefined) {
        const fmt = sigConfig?.format || "0.0";
        const unit = sigConfig?.unit || "";
        let display = typeof cv.value === "number"
          ? cv.value.toFixed(fmt.includes(".") ? fmt.split(".")[1].length : 1)
          : cv.value;
        el.textContent = `${display} ${unit}`;
        el.setAttribute("fill", cv.quality === "GOOD" ? "#22c55e" : "#ef4444");
      }
    });
  }, [currentValues, binding]);

  return (
    <div
      ref={containerRef}
      className="overflow-hidden rounded-lg"
      style={{ height: 500 }}
      onMouseDown={handleMouseDown}
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
      onMouseLeave={handleMouseUp}
    >
      {/* Zoom controls */}
      <div className="absolute top-2 right-2 z-10 flex gap-1">
        <button onClick={() => setZoom(z => Math.min(5, z + 0.2))}
          className="w-8 h-8 bg-gray-800 hover:bg-gray-700 rounded text-sm">+</button>
        <button onClick={() => setZoom(z => Math.max(0.2, z - 0.2))}
          className="w-8 h-8 bg-gray-800 hover:bg-gray-700 rounded text-sm">−</button>
        <button onClick={() => { setZoom(1); setPan({ x: 0, y: 0 }); }}
          className="px-2 h-8 bg-gray-800 hover:bg-gray-700 rounded text-xs">Reset</button>
      </div>

      <div
        ref={svgWrapperRef}
        style={{
          transform: `scale(${zoom}) translate(${pan.x / zoom}px, ${pan.y / zoom}px)`,
          transformOrigin: "0 0",
          cursor: dragging ? "grabbing" : "grab",
        }}
        dangerouslySetInnerHTML={{ __html: svgContent }}
      />
    </div>
  );
}
```

### 4. `README.md` — Full Run Instructions

Cập nhật README với hướng dẫn chạy đầy đủ. Giữ nguyên phần đầu (vision, philosophy), thêm section:

```markdown
## Quick Start

### Prerequisites

- Docker Desktop 4.30+
- Python 3.11+
- Node.js 20+

### 1. Start Infrastructure

```bash
docker compose -f deployment/docker-compose.yml up -d postgres tdengine
```

Wait for healthy (~20s):
```bash
docker ps --filter "name=plantos"
```

### 2. Setup Backend

```bash
cd backend
pip install -e ".[dev]"
alembic upgrade head
python scripts/seed_demo_plant.py
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Verify: `curl http://localhost:8000/health` → `{"status":"healthy"}`

### 3. Setup Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173

### 4. Run Simulator

```bash
cd edge/simulator
pip install -r requirements.txt
python simulator.py --config ../../examples/demo-plant/demo-plant.yaml
```

### 5. Run Tests

```bash
cd backend
python -m pytest tests/ -v
```

## Architecture

- **Backend**: FastAPI + PostgreSQL (metadata) + TDengine (time-series)
- **Frontend**: React + Vite + Tailwind CSS + shadcn/ui
- **Edge**: Python simulator → HTTP ingestion
- **API**: REST `/api/v1/*`, all data through API (no direct DB access)
- **Principles**: UNS-native, CDM-native, Asset/Signal binding

## MVP Features

- Asset & Signal Registry (CRUD)
- Measurement Ingestion & Query
- Historian (TDengine-backed)
- Dynamic SVG P&ID Diagram
- GIS Map with Asset Markers
- Trend Chart (multi-signal, ECharts)
- Edge Simulator (15 signals, 4 scenarios)
```

### 5. MVP Acceptance Criteria Checklist

Chạy và verify từng tiêu chí từ `docs/12-mvp-scope.md` §9:

```markdown
## MVP Acceptance Checklist

- [x] Demo plant loaded from sample data (seed_demo_plant.py)
- [x] Assets visible in UI (/assets page)
- [x] Signals visible in UI (/signals page)
- [x] Simulated measurements ingested (simulator → /api/v1/measurements/ingest)
- [x] Current value API returns latest values
- [x] Historical query API returns time-series data
- [x] Trend chart displays historical measurements
- [x] Dynamic diagram shows values/status
- [x] GIS map shows asset markers
- [x] All UI data through PlantOS APIs (no direct DB)
- [x] Documentation and run instructions available
```

## Constraints

- [x] Không bypass UNS/CDM
- [x] UI không query trực tiếp DB
- [x] Mọi data qua API

## Validation

```bash
# 1. Tests
cd backend && python -m pytest tests/ -v
# Expected: 44 passed

# 2. End-to-end
# Start all services → seed → simulator 30s →
# Check /assets, /signals, /historian, /diagrams, /gis

# 3. README
# Follow README quick start from scratch → all steps work
```

## Expected Output

1. Files modified: router.py, main.py, SvgDiagram.tsx, README.md
2. Test results: 44/44 PASSED
3. Zoom/pan works on diagram page
4. Live values display on diagram (after simulator running)
5. README has complete run instructions
6. MVP acceptance criteria all checked
7. Known limitations documented
