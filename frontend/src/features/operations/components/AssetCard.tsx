import { useQuery, useQueries } from "@tanstack/react-query";
import { Circle, AlertTriangle } from "lucide-react";
import { fetchAPI, getCurrentValues } from "@/lib/api";
import { useWorkspace } from "@/lib/WorkspaceContext";
import { useAssetSignals } from "../hooks/useAssetSignals";
import type { ThresholdConfig } from "../types";

interface Props {
  asset: { asset_id: string; name: string; asset_type: string; asset_role: string };
  onClick: () => void;
}

function formatVal(value: number | null | undefined): string {
  if (value === null || value === undefined) return "—";
  if (Math.abs(value) >= 1000) return value.toFixed(0);
  if (Math.abs(value) >= 1) return value.toFixed(1);
  return value.toFixed(2);
}

function deriveStatus(value: number | null | undefined, threshold: ThresholdConfig | null): "normal" | "warning" | "critical" {
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

export function AssetCard({ asset, onClick }: Props) {
  const { plantId } = useWorkspace();
  const { data: signals = [] } = useAssetSignals(asset.asset_id);

  // useQueries follows React hooks rules (no hooks in loops)
  const signalQueries = useQueries({
    queries: signals.map((s) => ({
      queryKey: ["current", s.signalId],
      queryFn: () =>
        getCurrentValues({ signal_id: s.signalId }).then((res: any) => {
          const arr = Array.isArray(res) ? res : [];
          return arr.length > 0 ? arr[0] : null;
        }),
      refetchInterval: 10000,
      enabled: signals.length > 0,
    })),
  });

  const signalValues = signals.map((s, i) => ({
    ...s,
    value: signalQueries[i]?.data?.value,
    timestamp: signalQueries[i]?.data?.timestamp,
  }));

  // Fetch alarms for this asset
  const { data: alarms } = useQuery({
    queryKey: ["alarms", asset.asset_id],
    queryFn: () => fetchAPI<any[]>(`/api/v1/alarms?asset_id=${asset.asset_id}&state=active`),
    refetchInterval: 15000,
  });
  const activeAlarms = (alarms || []).length;

  // Derive worst status across all signals
  const statuses = signalValues.map((sv) => deriveStatus(sv.value, null));
  const worstStatus = statuses.includes("critical") ? "critical" : statuses.includes("warning") ? "warning" : "normal";

  // Check if any signal has data (for freshness)
  const hasData = signalValues.some((sv) => sv.value !== undefined && sv.value !== null);

  return (
    <div
      onClick={onClick}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => { if (e.key === "Enter") onClick(); }}
      className="rounded-lg border cursor-pointer hover:brightness-110 transition-all flex flex-col"
      style={{
        backgroundColor: 'var(--surface-card)',
        borderColor: 'var(--border-default)',
        borderLeft: `3px solid ${STATUS_COLORS[worstStatus]}`,
        minHeight: 180,
      }}
    >
      {/* Top: name + badges */}
      <div className="p-3 border-b" style={{ borderColor: 'var(--border-subtle)' }}>
        <div className="text-sm font-semibold truncate" style={{ color: 'var(--text-primary)' }}>
          {asset.name || asset.asset_id}
        </div>
        <div className="flex gap-1 mt-1">
          <span
            className="text-[10px] px-1.5 py-0.5 rounded"
            style={{ backgroundColor: 'var(--surface-hover)', color: 'var(--text-muted)' }}
          >
            {asset.asset_type}
          </span>
          <span
            className="text-[10px] px-1.5 py-0.5 rounded"
            style={{ backgroundColor: 'var(--surface-hover)', color: 'var(--text-muted)' }}
          >
            {asset.asset_role}
          </span>
        </div>
      </div>

      {/* Middle: signal values */}
      <div className="flex-1 p-3 space-y-2">
        {signalValues.length === 0 && (
          <div className="text-xs" style={{ color: 'var(--text-muted)' }}>No signals configured</div>
        )}
        {signalValues.map((sv) => {
          const st = deriveStatus(sv.value, null);
          return (
            <div key={sv.signalId} className="flex items-center justify-between">
              <span className="text-xs" style={{ color: 'var(--text-secondary)' }}>{sv.label}</span>
              <span className="text-sm font-mono font-bold" style={{ color: st === "normal" ? 'var(--text-primary)' : STATUS_COLORS[st] }}>
                {formatVal(sv.value)}{sv.unit ? ` ${sv.unit}` : ""}
              </span>
            </div>
          );
        })}
      </div>

      {/* Bottom: alarm + freshness */}
      <div className="flex items-center justify-between px-3 py-2 border-t" style={{ borderColor: 'var(--border-subtle)' }}>
        <div className="flex items-center gap-1">
          {activeAlarms > 0 ? (
            <>
              <AlertTriangle className="w-3 h-3" style={{ color: 'var(--status-warning)' }} />
              <span className="text-xs" style={{ color: 'var(--status-warning)' }}>{activeAlarms} alarm{activeAlarms > 1 ? "s" : ""}</span>
            </>
          ) : (
            <span className="text-xs" style={{ color: 'var(--text-muted)' }}>✅ OK</span>
          )}
        </div>
        <div className="flex items-center gap-1">
          <Circle className="w-2 h-2 fill-current" style={{ color: hasData ? 'var(--status-normal)' : 'var(--status-offline)' }} />
          <span className="text-xs" style={{ color: 'var(--text-muted)' }}>{hasData ? "Live" : "Offline"}</span>
        </div>
      </div>
    </div>
  );
}
