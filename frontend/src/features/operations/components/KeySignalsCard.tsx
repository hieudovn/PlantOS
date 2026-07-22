import { useQueries } from "@tanstack/react-query";
import { Circle } from "lucide-react";
import { getCurrentValues } from "@/lib/api";
import type { AssetSignalConfig } from "../hooks/useAssetSignals";

interface Props {
  signalConfigs: AssetSignalConfig[];
}

function signalStatus(value: number | null | undefined, threshold: ThresholdConfig | null): "normal" | "warning" | "critical" {
  if (value === null || value === undefined) return "normal";
  if (!threshold) return "normal";
  if (threshold.direction === "high") {
    if (value >= threshold.crit) return "critical";
    if (value >= threshold.warn) return "warning";
  } else {
    if (value <= threshold.crit) return "critical";
    if (value <= threshold.warn) return "warning";
  }
  return "normal";
}

const STATUS_COLORS: Record<string, string> = {
  normal: "var(--status-normal)",
  warning: "var(--status-warning)",
  critical: "var(--status-critical)",
};

function formatVal(value: number | null | undefined): string {
  if (value === null || value === undefined) return "—";
  if (Math.abs(value) >= 1000) return value.toFixed(0);
  if (Math.abs(value) >= 1) return value.toFixed(1);
  return value.toFixed(2);
}

export function KeySignalsCard({ signalConfigs }: Props) {
  const signalIds = signalConfigs.map((s) => s.signalId);

  const queries = useQueries({
    queries: signalIds.map((sid) => ({
      queryKey: ["current-keysig", sid],
      queryFn: () =>
        getCurrentValues({ signal_id: sid }).then((res: any) => {
          const arr = Array.isArray(res) ? res : [];
          return arr.length > 0 ? arr[0] : null;
        }),
      refetchInterval: 10000,
      enabled: signalIds.length > 0,
    })),
  });

  if (signalConfigs.length === 0) {
    return (
      <div
        className="rounded-lg border p-4"
        style={{ backgroundColor: 'var(--surface-card)', borderColor: 'var(--border-default)' }}
      >
        <h3 className="text-sm font-semibold mb-2" style={{ color: 'var(--text-secondary)' }}>Key Signals</h3>
        <div className="text-xs" style={{ color: 'var(--text-muted)' }}>No signals configured for this asset.</div>
      </div>
    );
  }

  return (
    <div
      className="rounded-lg border p-4"
      style={{ backgroundColor: 'var(--surface-card)', borderColor: 'var(--border-default)' }}
    >
      <h3 className="text-sm font-semibold mb-3" style={{ color: 'var(--text-secondary)' }}>Key Signals</h3>
      <div className="space-y-2">
        {signalConfigs.map((sc, i) => {
          const value = queries[i]?.data?.value;
          const status = signalStatus(value, null);
          return (
            <div key={sc.signalId} className="flex items-center justify-between">
              <span className="text-xs" style={{ color: 'var(--text-muted)' }}>{sc.label}</span>
              <div className="flex items-center gap-2">
                <span className="text-sm font-mono font-bold" style={{ color: status === "normal" ? 'var(--text-primary)' : STATUS_COLORS[status] }}>
                  {formatVal(value)}{sc.unit ? ` ${sc.unit}` : ""}
                </span>
                <Circle className="w-2 h-2 fill-current" style={{ color: STATUS_COLORS[status] }} />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
