import { useQuery } from "@tanstack/react-query";
import { CheckCircle, AlertTriangle, XCircle, Circle } from "lucide-react";
import { getCurrentValues } from "@/lib/api";

type ThresholdConfig = { warn: number; crit: number; direction: "high" | "low" } | null;

export interface ProcessBlockConfig {
  id: string;
  label: string;
  areaId: string;
  signalId: string;
  unit: string;
}

interface Props {
  config: ProcessBlockConfig;
  onClick: () => void;
}

type Status = "normal" | "warning" | "critical";

const STATUS_ICONS = {
  normal: CheckCircle,
  warning: AlertTriangle,
  critical: XCircle,
};

const STATUS_COLORS = {
  normal: "var(--status-normal)",
  warning: "var(--status-warning)",
  critical: "var(--status-critical)",
};

function deriveStatus(value: number | null | undefined, threshold: ThresholdConfig | null): Status {
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

function formatBlockValue(value: number | null | undefined): string {
  if (value === null || value === undefined) return "—";
  if (Math.abs(value) >= 1000) return value.toFixed(0);
  if (Math.abs(value) >= 1) return value.toFixed(1);
  return value.toFixed(2);
}

export function ProcessBlock({ config, onClick }: Props) {
  const { data } = useQuery({
    queryKey: ["current-single", config.signalId],
    queryFn: () =>
      getCurrentValues({ signal_id: config.signalId }).then((res: any) => {
        const arr = Array.isArray(res) ? res : [];
        return arr.length > 0 ? arr[0] : null;
      }),
    refetchInterval: 10000,
  });

  const value = data?.value;
  const status = deriveStatus(value, null);
  const StatusIcon = STATUS_ICONS[status];

  return (
    <div
      onClick={onClick}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => { if (e.key === "Enter") onClick(); }}
      className="w-40 h-32 rounded-lg border cursor-pointer hover:brightness-110 transition-all flex flex-col justify-between p-3"
      style={{
        backgroundColor: 'var(--surface-card)',
        borderColor: 'var(--border-default)',
        borderLeft: `3px solid ${STATUS_COLORS[status]}`,
      }}
    >
      {/* Header */}
      <div className="flex items-center gap-1.5 min-w-0">
        <StatusIcon className="w-4 h-4 shrink-0" style={{ color: STATUS_COLORS[status] }} />
        <span className="text-sm font-medium truncate" style={{ color: 'var(--text-primary)' }}>
          {config.label}
        </span>
      </div>

      {/* KPI value */}
      <div className="flex items-baseline gap-1">
        <span className="text-xl font-bold leading-tight" style={{ color: 'var(--text-primary)' }}>
          {formatBlockValue(value)}
        </span>
        <span className="text-xs" style={{ color: 'var(--text-muted)' }}>{config.unit}</span>
      </div>

      {/* Data freshness */}
      <div className="flex items-center gap-1">
        <Circle className="w-2 h-2 fill-current" style={{ color: data ? 'var(--status-normal)' : 'var(--status-offline)' }} />
        <span className="text-xs" style={{ color: 'var(--text-muted)' }}>{data ? "Live" : "Offline"}</span>
      </div>
    </div>
  );
}