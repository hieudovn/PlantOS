import { useState, useEffect } from "react";
import { SvgDiagram } from "./SvgDiagram";
import { useWorkspace } from "@/lib/WorkspaceContext";

const PLANT_DIAGRAMS: Record<string, Array<{ id: string; name: string; svg: string }>> = {
  "VF-DEMO": [
    { id: "pid-process", name: "P&amp;ID Process Line 01", svg: "/diagrams/pid-process.svg" },
    { id: "one-line-electrical", name: "One-Line Electrical", svg: "/diagrams/one-line-electrical.svg" },
  ],
  "WTP-DEMO-01": [
    { id: "wtp-process", name: "WTP Process Flow", svg: "/diagrams/wtp-demo-01-process.svg" },
  ],
};

function getDiagramsForPlant(plantId: string | null) {
  return PLANT_DIAGRAMS[plantId || ""] || [];
}

async function loadBinding(id: string): Promise<any> {
  try {
    const resp = await fetch(`/diagrams/${id}.binding.yaml`);
    const text = await resp.text();
    // Simple YAML parsing for flat binding files (MVP only)
    // In production, use js-yaml
    const binding: any = { signals: [], states: [], state_styles: {} };
    const lines = text.split("\n");
    let section = "";
    for (const line of lines) {
      const trimmed = line.trim();
      if (trimmed.startsWith("signals:") && !trimmed.includes("signal_name")) section = "signals";
      else if (trimmed === "states:") section = "states";
      else if (trimmed === "state_styles:") section = "state_styles";
      else if (trimmed.startsWith("refresh_interval_ms:")) binding.refresh_interval_ms = parseInt(trimmed.split(":")[1]);
      else if (section === "signals" && trimmed.startsWith("- asset_id:")) {
        const assetId = trimmed.split(":").slice(1).join(":").trim();
        const sig: any = { asset_id: assetId };
        binding.signals.push(sig);
      } else if (section === "signals" && binding.signals.length > 0) {
        const last = binding.signals[binding.signals.length - 1];
        if (trimmed.startsWith("signal_name:")) last.signal_name = trimmed.split(":").slice(1).join(":").trim();
        else if (trimmed.startsWith("format:")) last.format = trimmed.split(":").slice(1).join(":").trim();
        else if (trimmed.startsWith("unit:")) last.unit = trimmed.split(":").slice(1).join(":").trim();
      } else if (section === "states" && trimmed.startsWith("- asset_id:")) {
        binding.states.push({ asset_id: trimmed.split(":").slice(1).join(":").trim() });
      }
    }
    return binding;
  } catch {
    return { signals: [], states: [], refresh_interval_ms: 5000 };
  }
}

export function DiagramPage() {
  const { plantId: currentPlantId } = useWorkspace();
  const diagrams = getDiagramsForPlant(currentPlantId);
  const [diagramId, setDiagramId] = useState(diagrams.length > 0 ? diagrams[0].id : "");
  const [binding, setBinding] = useState<any>(null);
  const diagram = diagrams.find(d => d.id === diagramId) || diagrams[0];

  useEffect(() => {
    if (diagramId) {
      loadBinding(diagramId).then(setBinding);
    }
  }, [diagramId]);

  if (diagrams.length === 0) {
    return (
      <div className="space-y-4">
        <h1 className="text-2xl font-bold">Diagrams</h1>
        <div className="text-gray-500 text-center py-16">
          No diagrams configured for this plant
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Diagrams</h1>
        <select
          value={diagramId}
          onChange={e => setDiagramId(e.target.value)}
          className="bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm"
        >
          {diagrams.map(d => (
            <option key={d.id} value={d.id}>{d.name}</option>
          ))}
        </select>
      </div>
      <div className="bg-gray-900/50 rounded-lg border border-gray-800 p-4">
        {binding ? (
          <SvgDiagram svgUrl={diagram.svg} binding={binding} />
        ) : (
          <div className="text-gray-500 py-8 text-center">Loading diagram...</div>
        )}
      </div>
    </div>
  );
}
