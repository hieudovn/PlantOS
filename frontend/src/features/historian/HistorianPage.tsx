import { useState, useEffect, useRef } from "react";
import { SignalMultiSelect } from "./SignalMultiSelect";
import { TrendChart } from "./TrendChart";
import { Plus, X } from "lucide-react";

const STORAGE_KEY = "plantos-historian-state";

function fmt(date: Date) {
  const y = date.getFullYear();
  const mo = String(date.getMonth() + 1).padStart(2, "0");
  const d = String(date.getDate()).padStart(2, "0");
  const h = String(date.getHours()).padStart(2, "0");
  const mi = String(date.getMinutes()).padStart(2, "0");
  return `${y}-${mo}-${d}T${h}:${mi}`;
}

function loadState() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) return JSON.parse(raw);
  } catch {
    /* ignore */
  }
  return null;
}

function saveState(state: any) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  } catch {
    /* ignore */
  }
}

interface Panel {
  id: number;
  signalIds: string[];
  label: string;
}

const defaultPanels: Panel[] = [{ id: 1, signalIds: [], label: "Chart 1" }];

export function HistorianPage() {
  const saved = loadState();
  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());

  const [from, setFrom] = useState(saved?.from ?? fmt(today));
  const [to, setTo] = useState(saved?.to ?? fmt(now));
  const [preset, setPreset] = useState<string | null>(saved?.preset ?? null);
  const [panels, setPanels] = useState<Panel[]>(saved?.panels ?? defaultPanels);
  const [active, setActive] = useState(saved?.active ?? 0);
  const [chartType, setChartType] = useState(saved?.chartType ?? "line");
  const [editingTab, setEditingTab] = useState<number | null>(null);
  const [editValue, setEditValue] = useState("");
  const editInputRef = useRef<HTMLInputElement>(null);

  // Apply a time range preset: update from/to relative to now
  const applyPreset = (p: string | null) => {
    setPreset(p);
    if (p) {
      const n = new Date();
      const toStr = fmt(n);
      const dur: Record<string, number> = {
        "10m": 10 * 60 * 1000,
        "30m": 30 * 60 * 1000,
        "1h": 60 * 60 * 1000,
        "6h": 6 * 60 * 60 * 1000,
        "12h": 12 * 60 * 60 * 1000,
      };
      const ms = dur[p];
      if (ms) {
        setFrom(fmt(new Date(n.getTime() - ms)));
        setTo(toStr);
      }
    }
  };

  // Auto-refresh from/to when a preset is active (every 10s)
  useEffect(() => {
    if (!preset) return;
    const id = setInterval(() => applyPreset(preset), 10000);
    return () => clearInterval(id);
  }, [preset]);

  // Auto-save state to localStorage
  useEffect(() => {
    saveState({ from, to, preset, panels, active, chartType });
  }, [from, to, preset, panels, active, chartType]);

  // Focus edit input when tab editing starts
  useEffect(() => {
    if (editingTab !== null) {
      editInputRef.current?.focus();
      editInputRef.current?.select();
    }
  }, [editingTab]);

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

  const commitRename = (i: number) => {
    if (editValue.trim()) {
      const np = [...panels];
      np[i].label = editValue.trim();
      setPanels(np);
    }
    setEditingTab(null);
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
            onChange={e => { setFrom(e.target.value); setPreset(null); }}
            className="bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm"
          />
        </div>
        <div>
          <label className="block text-xs text-gray-500 mb-1">To</label>
          <input
            type="datetime-local"
            value={to}
            onChange={e => { setTo(e.target.value); setPreset(null); }}
            className="bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm"
          />
        </div>

        <div>
          <label className="block text-xs text-gray-500 mb-1">Range</label>
          <div className="flex gap-1">
            {[
              { key: "10m", label: "10p" },
              { key: "30m", label: "30p" },
              { key: "1h", label: "1h" },
              { key: "6h", label: "6h" },
              { key: "12h", label: "12h" },
            ].map(({ key, label }) => (
              <button
                key={key}
                onClick={() => applyPreset(key)}
                className={`px-2 py-1.5 text-xs rounded transition-colors ${
                  preset === key
                    ? "bg-blue-600 text-white"
                    : "bg-gray-800 text-gray-400 hover:text-white hover:bg-gray-700"
                }`}
              >
                {label}
              </button>
            ))}
            {preset && (
              <button
                onClick={() => applyPreset(null)}
                className="px-2 py-1.5 text-xs rounded bg-gray-800 text-gray-500 hover:text-white"
                title="Custom range"
              >
                ✕
              </button>
            )}
          </div>
        </div>
        <div>
          <label className="block text-xs text-gray-500 mb-1">Chart Type</label>
          <select
            value={chartType}
            onChange={e => setChartType(e.target.value)}
            className="bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm"
          >
            <option value="line">Line</option>
            <option value="bar">Bar</option>
            <option value="scatter">Scatter</option>
            <option value="area">Area</option>
          </select>
        </div>
        <span className="text-xs text-gray-600">
          {panels.reduce((s, p) => s + p.signalIds.length, 0)} signals
        </span>
        {preset && (
          <span className="flex items-center gap-1.5 text-xs text-green-400 font-medium">
            <span className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
            Live
          </span>
        )}
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
            {editingTab === i ? (
              <input
                ref={editInputRef}
                value={editValue}
                onChange={e => setEditValue(e.target.value)}
                onBlur={() => commitRename(i)}
                onKeyDown={e => {
                  if (e.key === "Enter") e.currentTarget.blur();
                  if (e.key === "Escape") setEditingTab(null);
                }}
                className="bg-gray-800 px-1 py-0 text-sm w-24 outline-none"
                onClick={e => e.stopPropagation()}
              />
            ) : (
              <span
                onDoubleClick={() => {
                  setEditingTab(i);
                  setEditValue(p.label);
                }}
              >
                {p.label}
              </span>
            )}
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
          chartType={chartType}
        />
      </div>
    </div>
  );
}
