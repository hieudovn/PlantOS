# Phase 2 — Task 2-04: WebSocket Real-time Updates

> **Designer:** DeepSeek V4 Pro | **Date:** 2026-06-30

## Context

Thay polling (`refetchInterval`) bằng WebSocket real-time push. Khi simulator/agent gửi measurement → backend broadcast qua WebSocket → frontend cập nhật Asset Detail + Diagram values tức thì.

## Architecture

```
Simulator/Agent → HTTP POST /api/v1/measurements/ingest
       │
       ▼
Backend Historian (write)
       │
       ▼
WebSocket broadcast ──→ Frontend clients (AssetDetail, SvgDiagram)
```

## Implementation Checklist

- [ ] CREATE `backend/app/api/ws.py` — WebSocket endpoint + broadcast manager
- [ ] MODIFY `backend/app/main.py` — mount WebSocket route
- [ ] MODIFY `backend/app/modules/measurements/router.py` — broadcast after ingest
- [ ] CREATE `frontend/src/lib/useRealtimeValues.ts` — WebSocket hook
- [ ] MODIFY `frontend/src/features/assets/AssetDetail.tsx` — use WebSocket
- [ ] MODIFY `frontend/src/features/visualization/SvgDiagram.tsx` — use WebSocket

## Detailed Instructions

### 1. `backend/app/api/ws.py` — WebSocket Broadcast

```python
"""WebSocket endpoint for real-time measurement updates."""

import asyncio
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()

# Connected clients
_clients: set[WebSocket] = set()


@router.websocket("/ws/measurements")
async def ws_measurements(ws: WebSocket):
    await ws.accept()
    _clients.add(ws)
    try:
        while True:
            # Keep-alive: wait for any message or ping
            await ws.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        _clients.discard(ws)


async def broadcast_measurements(measurements: list[dict]):
    """Broadcast new measurements to all connected WebSocket clients."""
    if not _clients:
        return
    payload = json.dumps({"type": "measurements", "data": measurements})
    dead: set[WebSocket] = set()
    for ws in _clients:
        try:
            await ws.send_text(payload)
        except Exception:
            dead.add(ws)
    _clients -= dead
```

### 2. `backend/app/main.py` — Mount WebSocket

```python
from app.api.ws import router as ws_router
app.include_router(ws_router)
```

### 3. `backend/app/modules/measurements/router.py` — Broadcast

Sau khi ingest thành công, broadcast measurements:

```python
from app.api.ws import broadcast_measurements

@router.post("/measurements/ingest", response_model=IngestResponse)
async def ingest_measurements(data: IngestRequest, historian: HistorianInterface = Depends(get_historian)):
    service = MeasurementService(historian)
    result = await service.ingest(data)

    # Broadcast accepted measurements to WebSocket clients
    if result.accepted > 0:
        # Filter only accepted measurements
        valid_ids = {m.signal_id for m in data.measurements if ...}  # already validated in service
        ws_data = [
            {"timestamp": m.timestamp, "signal_id": m.signal_id, "value": m.value, "quality": m.quality}
            for m in data.measurements
        ]
        await broadcast_measurements(ws_data)

    return result
```

> **Coder:** Tối ưu — chỉ broadcast measurements đã được accepted. Dùng `asyncio.create_task(broadcast_measurements(...))` để không block response.

### 4. `frontend/src/lib/useRealtimeValues.ts` — WebSocket Hook

```tsx
import { useEffect, useRef, useState, useCallback } from "react";

interface Measurement {
  timestamp: string;
  signal_id: string;
  value: number | boolean;
  quality: string;
}

type ValueMap = Record<string, Measurement>;

export function useRealtimeValues(assetIds: string[]) {
  const [values, setValues] = useState<ValueMap>({});
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectRef = useRef<ReturnType<typeof setTimeout>>();

  const connect = useCallback(() => {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const host = window.location.host;
    const ws = new WebSocket(`${protocol}//${host}/ws/measurements`);

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        if (msg.type === "measurements") {
          setValues(prev => {
            const next = { ...prev };
            for (const m of msg.data) {
              next[m.signal_id] = m;
            }
            return next;
          });
        }
      } catch {}
    };

    ws.onclose = () => {
      reconnectRef.current = setTimeout(connect, 3000);
    };

    wsRef.current = ws;
  }, []);

  useEffect(() => {
    connect();
    return () => {
      wsRef.current?.close();
      clearTimeout(reconnectRef.current);
    };
  }, [connect]);

  // Also fetch initial values via HTTP
  useEffect(() => {
    if (assetIds.length === 0) return;
    import("@/lib/api").then(({ getCurrentValues }) => {
      assetIds.forEach(async (aid) => {
        try {
          const vals = await getCurrentValues({ asset_id: aid });
          vals?.forEach((v: any) => {
            setValues(prev => ({ ...prev, [v.signal_id]: v }));
          });
        } catch {}
      });
    });
  }, [assetIds.join(",")]);

  return values;
}
```

### 5. `AssetDetail.tsx` — Replace polling with WebSocket

```tsx
import { useRealtimeValues } from "@/lib/useRealtimeValues";

// Replace:
// const { data: currentValues } = useQuery({ queryKey: ["current", assetId], refetchInterval: 5000, ... });
// With:
const currentValues = useRealtimeValues(assetId ? [assetId] : []);

// Build currentMap from realtime values
const currentMap = currentValues;
```

### 6. `SvgDiagram.tsx` — Replace polling with WebSocket

```tsx
import { useRealtimeValues } from "@/lib/useRealtimeValues";

// Replace the useQuery for diagram-values with:
const currentValues = useRealtimeValues(assetIds as string[]);
```

Remove `refetchInterval` from the old `useQuery` call — WebSocket replaces it.

## Constraints

- [x] WebSocket fallback: reconnect sau 3s nếu mất kết nối
- [x] Initial data: fetch HTTP khi mount (đề phòng WebSocket chưa kịp)
- [x] Không bypass API — WebSocket chỉ broadcast data đã qua ingest
- [x] Backend broadcast non-blocking (`asyncio.create_task`)

## Validation

```bash
# 1. Start backend + frontend
# 2. Open Asset Detail page
# 3. Run simulator → giá trị tự update không cần refresh
python edge/simulator/simulator.py --duration 30

# 4. Open Diagram page → values tự update trên SVG
```

## Files

| # | File | Action |
|---|------|--------|
| 1 | `backend/app/api/ws.py` | CREATE |
| 2 | `backend/app/main.py` | MODIFY |
| 3 | `backend/app/modules/measurements/router.py` | MODIFY |
| 4 | `frontend/src/lib/useRealtimeValues.ts` | CREATE |
| 5 | `frontend/src/features/assets/AssetDetail.tsx` | MODIFY |
| 6 | `frontend/src/features/visualization/SvgDiagram.tsx` | MODIFY |
