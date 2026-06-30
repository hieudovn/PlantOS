import { useEffect, useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { getCurrentValues } from "@/lib/api";

type Props = { svgUrl: string; binding: any };

export function SvgDiagram({ svgUrl, binding }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [svgContent, setSvgContent] = useState<string>("");

  // Fetch SVG file
  useEffect(() => {
    fetch(svgUrl)
      .then(r => r.text())
      .then(setSvgContent)
      .catch(() => setSvgContent("<p class='text-red-400'>Failed to load SVG</p>"));
  }, [svgUrl]);

  // Collect unique asset_ids from binding
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

  // Update SVG DOM with current values
  useEffect(() => {
    if (!containerRef.current || !currentValues) return;
    const container = containerRef.current;

    // Update state styles
    container.querySelectorAll("[data-binding='state']").forEach((el: any) => {
      const g = el.closest("[data-asset-id]") as HTMLElement;
      const assetId = g?.getAttribute("data-asset-id");
      if (!assetId) return;
      const style = binding.state_styles?.default || {};
      Object.entries(style).forEach(([k, v]) => { el.setAttribute(k, v as string); });
    });

    // Update signal values
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
        let display =
          typeof cv.value === "number"
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
      className="flex justify-center overflow-auto"
      dangerouslySetInnerHTML={{ __html: svgContent }}
    />
  );
}
