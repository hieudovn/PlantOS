import { useEffect, useRef, useState, useCallback } from "react";
import { useRealtimeValues } from "@/lib/useRealtimeValues";

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

  const handleMouseDown = useCallback(
    (e: React.MouseEvent) => {
      if (e.button !== 0) return;
      setDragging(true);
      dragStart.current = { x: e.clientX - pan.x, y: e.clientY - pan.y };
    },
    [pan]
  );

  const handleMouseMove = useCallback(
    (e: React.MouseEvent) => {
      if (!dragging) return;
      setPan({
        x: e.clientX - dragStart.current.x,
        y: e.clientY - dragStart.current.y,
      });
    },
    [dragging]
  );

  const handleMouseUp = useCallback(() => setDragging(false), []);

  // Attach wheel listener
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
      .catch(() =>
        setSvgContent("<p class='text-red-400 p-4'>Failed to load SVG</p>")
      );
  }, [svgUrl]);

  // ---- Live Data via WebSocket ----
  const assetIds = [
    ...new Set(binding.signals?.map((s: any) => s.asset_id) || []),
  ];

  const currentValues = useRealtimeValues(assetIds as string[]);

  // Update SVG DOM with current values
  useEffect(() => {
    if (!containerRef.current || !currentValues) return;
    const container = containerRef.current;

    container
      .querySelectorAll("[data-binding='state']")
      .forEach((el: any) => {
        const g = el.closest("[data-asset-id]") as HTMLElement;
        const assetId = g?.getAttribute("data-asset-id");
        if (!assetId) return;
        const style = binding.state_styles?.default || {};
        Object.entries(style).forEach(([k, v]) => {
          el.setAttribute(k, v as string);
        });
      });

    container
      .querySelectorAll("[data-binding='signal_value']")
      .forEach((el: any) => {
        const signalName = el.getAttribute("data-signal-name");
        const assetId = el.getAttribute("data-asset-id");
        if (!signalName) return;
        const key = `${assetId}.${signalName}`;
        const cv = currentValues[key];
        const sigConfig = binding.signals?.find(
          (s: any) =>
            s.signal_name === signalName && s.asset_id === assetId
        );

        if (cv && cv.value !== null && cv.value !== undefined) {
          const fmt = sigConfig?.format || "0.0";
          const unit = sigConfig?.unit || "";
          const display =
            typeof cv.value === "number"
              ? cv.value.toFixed(
                  fmt.includes(".") ? fmt.split(".")[1].length : 1
                )
              : cv.value;
          el.textContent = `${display} ${unit}`;
          el.setAttribute(
            "fill",
            cv.quality === "GOOD" ? "#22c55e" : "#ef4444"
          );
        }
      });
  }, [currentValues, binding]);

  return (
    <div
      ref={containerRef}
      className="overflow-hidden rounded-lg relative"
      style={{ height: 500 }}
      onMouseDown={handleMouseDown}
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
      onMouseLeave={handleMouseUp}
    >
      {/* Zoom controls */}
      <div className="absolute top-2 right-2 z-10 flex gap-1">
        <button
          onClick={() => setZoom(z => Math.min(5, z + 0.2))}
          className="w-8 h-8 bg-gray-800 hover:bg-gray-700 rounded text-sm"
        >
          +
        </button>
        <button
          onClick={() => setZoom(z => Math.max(0.2, z - 0.2))}
          className="w-8 h-8 bg-gray-800 hover:bg-gray-700 rounded text-sm"
        >
          −
        </button>
        <button
          onClick={() => {
            setZoom(1);
            setPan({ x: 0, y: 0 });
          }}
          className="px-2 h-8 bg-gray-800 hover:bg-gray-700 rounded text-xs"
        >
          Reset
        </button>
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
