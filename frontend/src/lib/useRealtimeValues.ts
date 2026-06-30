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
      } catch {
        /* ignore malformed messages */
      }
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
        } catch {
          /* ignore */
        }
      });
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [assetIds.join(",")]);

  return values;
}
