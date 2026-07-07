import { useQuery } from "@tanstack/react-query";
import { CheckCircle, AlertTriangle, XCircle, Circle } from "lucide-react";
import { getCurrentValues } from "@/lib/api";

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

const THRESHOLDS: Record<string, { warn: number; crit: number; direction: "high" | "low" }> = {
  "RWP-101.flow_rate": { warn: 400, crit: 200, direction: "low" },
  "CHEMICAL-CONSUMPTION-STATION-101.coagulant_dose_rate": { warn: 50, crit: 80, direction: "high" },
  "CLARIFIER-101.settled_turbidity": { warn: 5, crit: 10, direction: "high" },
  "FILTER-QUALITY-STATION-101.filtered_turbidity": { warn: 0.5, crit: 1, direction: "high" },
  "DISINFECTION-QUALITY-STATION-101.free_chlorine": { warn: 0.8, crit: 0.5, direction: "low" },
  "CLEAR-WATER-TANK-101.level": { warn: 30, crit: 15, direction: "low" },
  "HSP-101.flow_rate": { warn: 300, crit: 150, direction: "low" },
};

function deriveStatus(signalId: string, value: number | null | undefined): Status {
  if (value === null || value === undefined) return "normal";
  const t = THRESHOLDS[signalId];
  if (!t) return "normal";
  if (t.direction === "high") {
    if (value >= t.crit) return "critical";
    if (value >= t.warn) return "warning";
  } else {
    if (value <= t.crit) return "critical";
    if (value <= t.warn) return "warning";
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
  const status = deriveStatus(config.signalId, value);
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