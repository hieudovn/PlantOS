import { useState } from "react";
import { SignalMultiSelect } from "./SignalMultiSelect";
import { TrendChart } from "./TrendChart";
import { Plus, X } from "lucide-react";

function fmt(iso: string) {
  return iso.substring(0, 16);
}

interface Panel {
  id: number;
  signalIds: string[];
  label: string;
}

export function HistorianPage() {
  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const [from, setFrom] = useState(fmt(today.toISOString()));
  const [to, setTo] = useState(fmt(now.toISOString()));
  const [panels, setPanels] = useState<Panel[]>([
    { id: 1, signalIds: [], label: "Chart 1" },
  ]);
  const [active, setActive] = useState(0);

  const addPanel = () => {
    const id = Math.max(0, ...panels.map(p => p.id)) + 1;
    setPanels([...panels, { id, signalIds: [], label: `Chart ${id}` }]);
    setActive(panels.length);
  };

  const removePanel = (i: number) => {
    if (panels.length <= 1) return;
    const np = panels.filter((_, j) => j !== i);
    setPanels(np);
    setActive(Math.min(active, np.length - 1));
  };

  const updateSignals = (i: number, ids: string[]) => {
    const np = [...panels];
    np[i] = {
      ...np[i],
      signalIds: ids,
      label:
        ids.length > 0
          ? ids[0].split(".").pop() || ids[0]
          : np[i].label,
    };
    setPanels(np);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Historian</h1>
        <button
          onClick={addPanel}
          className="flex items-center gap-1 px-3 py-1.5 bg-gray-800 hover:bg-gray-700 rounded text-sm"
        >
          <Plus className="w-4 h-4" /> Add Chart
        </button>
      </div>

      <div className="flex gap-4 items-end">
        <div>
          <label className="block text-xs text-gray-500 mb-1">From</label>
          <input
            type="datetime-local"
            value={from}
            onChange={e => setFrom(e.target.value)}
            className="bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm"
          />
        </div>
        <div>
          <label className="block text-xs text-gray-500 mb-1">To</label>
          <input
            type="datetime-local"
            value={to}
            onChange={e => setTo(e.target.value)}
            className="bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm"
          />
        </div>
        <span className="text-xs text-gray-600">
          {panels.reduce((s, p) => s + p.signalIds.length, 0)} signals
        </span>
      </div>

      <div className="flex border-b border-gray-800 gap-1">
        {panels.map((p, i) => (
          <button
            key={p.id}
            onClick={() => setActive(i)}
            className={`flex items-center gap-2 px-4 py-2 text-sm rounded-t ${
              i === active
                ? "bg-gray-900 border border-gray-800 border-b-transparent text-white"
                : "text-gray-500 hover:text-gray-300"
            }`}
          >
            {p.label}
            {panels.length > 1 && (
              <span
                onClick={e => {
                  e.stopPropagation();
                  removePanel(i);
                }}
                className="hover:text-red-400"
              >
                <X className="w-3 h-3" />
              </span>
            )}
          </button>
        ))}
      </div>

      <SignalMultiSelect
        selected={panels[active]?.signalIds || []}
        onChange={ids => updateSignals(active, ids)}
      />

      <div className="bg-gray-900/50 rounded-lg border border-gray-800 p-4">
        <TrendChart
          signalIds={panels[active]?.signalIds || []}
          from={new Date(from).toISOString()}
          to={new Date(to).toISOString()}
        />
      </div>
    </div>
  );
}
