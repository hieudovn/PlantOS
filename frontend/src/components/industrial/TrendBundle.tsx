import { useState, useMemo } from "react";
import { TrendChart } from "@/features/historian/TrendChart";

type SignalDef = {
  signalId: string;
  label: string;
  color?: string;
  unit?: string;
};

type TrendBundleProps = {
  title: string;
  description?: string;
  signals: SignalDef[];
  defaultTimeRange?: "10m" | "30m" | "1h" | "6h" | "12h";
  height?: number;
  refetchInterval?: number;
};

const TIME_RANGES = [
  { key: "10m", label: "10m" },
  { key: "30m", label: "30m" },
  { key: "1h", label: "1h" },
  { key: "6h", label: "6h" },
  { key: "12h", label: "12h" },
] as const;

function getTimeRange(key: string): { from: string; to: string } {
  const now = new Date();
  const to = now.toISOString();
  const from = new Date(now.getTime() - (() => {
    switch (key) {
      case "10m": return 10 * 60 * 1000;
      case "30m": return 30 * 60 * 1000;
      case "1h": return 60 * 60 * 1000;
      case "6h": return 6 * 60 * 60 * 1000;
      case "12h": return 12 * 60 * 60 * 1000;
      default: return 60 * 60 * 1000;
    }
  })()).toISOString();
  return { from, to };
}

export function TrendBundle({
  title,
  description,
  signals,
  defaultTimeRange = "10m",
  height = 200,
  refetchInterval,
}: TrendBundleProps) {
  const [timeRange, setTimeRange] = useState(defaultTimeRange);
  const { from, to } = useMemo(() => getTimeRange(timeRange), [timeRange]);
  const signalIds = signals.map((s) => s.signalId);

  return (
    <div style={{ backgroundColor: 'var(--surface-card)', borderColor: 'var(--border-default)' }} className="rounded-lg border p-4">
      <div className="flex items-center justify-between mb-2">
        <div>
          <h3 className="text-xs font-semibold uppercase tracking-wide" style={{ color: 'var(--text-secondary)' }}>{title}</h3>
          {description && <span className="text-xs" style={{ color: 'var(--text-muted)' }}>{description}</span>}
        </div>
        <div className="flex gap-1">
          {TIME_RANGES.map((r) => (
            <button key={r.key} onClick={() => setTimeRange(r.key)}
              className="text-xs px-1.5 py-0.5 rounded transition-colors"
              style={{
                backgroundColor: timeRange === r.key ? 'var(--surface-hover)' : 'transparent',
                color: timeRange === r.key ? 'var(--text-primary)' : 'var(--text-muted)',
                border: timeRange === r.key ? '1px solid var(--border-default)' : '1px solid transparent',
              }}>{r.label}</button>
          ))}
        </div>
      </div>

      <div className="flex flex-wrap gap-3 mb-1">
        {signals.map((s) => (
          <span key={s.signalId} className="inline-flex items-center gap-1 text-xs">
            <span className="w-2 h-2 rounded-full inline-block" style={{ backgroundColor: s.color || '#3b82f6' }} />
            <span style={{ color: 'var(--text-muted)' }}>{s.label}</span>
            {s.unit && <span style={{ color: 'var(--text-muted)' }} className="opacity-60">({s.unit})</span>}
          </span>
        ))}
      </div>

      {signalIds.length > 0 ? (
        <div style={{ height, overflow: "hidden" }}>
          <TrendChart signalIds={signalIds} from={from} to={to} showLegend={false} showToolbox={false} refetchInterval={refetchInterval} height={height} compact />
        </div>
      ) : (
        <div className="flex items-center justify-center" style={{ height, color: 'var(--text-muted)' }}>
          <span className="text-xs">No signals configured</span>
        </div>
      )}
    </div>
  );
}
