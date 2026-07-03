import { TrendingUp, TrendingDown, Minus } from "lucide-react";
import { DataQualityBadge } from "./DataQualityBadge";

type KpiCardProps = {
  label: string;
  value: string | number;
  unit?: string;
  state?: "normal" | "warning" | "critical" | "offline";
  trend?: "up" | "down" | "flat";
  trendLabel?: string;
  quality?: string;
  timestamp?: string;
  onClick?: () => void;
};

const stateBorder: Record<string, string> = {
  warning: "3px solid var(--status-warning)",
  critical: "3px solid var(--status-critical)",
  offline: "3px solid var(--status-offline)",
};

const trendIcon: Record<string, JSX.Element> = {
  up: <TrendingUp className="w-3 h-3" style={{ color: 'var(--status-normal)' }} />,
  down: <TrendingDown className="w-3 h-3" style={{ color: 'var(--status-critical)' }} />,
  flat: <Minus className="w-3 h-3" style={{ color: 'var(--text-muted)' }} />,
};

export function KpiCard({
  label,
  value,
  unit,
  state,
  trend,
  trendLabel,
  quality,
  timestamp,
  onClick,
}: KpiCardProps) {
  return (
    <div
      onClick={onClick}
      role={onClick ? "button" : undefined}
      tabIndex={onClick ? 0 : undefined}
      onKeyDown={onClick ? (e) => { if (e.key === "Enter") onClick(); } : undefined}
      style={{
        backgroundColor: 'var(--surface-card)',
        borderColor: 'var(--border-default)',
        borderLeft: state ? stateBorder[state] || undefined : undefined,
      }}
      className={`rounded-lg p-4 border ${onClick ? "cursor-pointer hover:brightness-110 transition-all" : ""}`}
    >
      <div style={{ color: 'var(--text-secondary)' }} className="text-xs mb-1">
        {label}
      </div>
      <div className="flex items-baseline gap-1">
        <span style={{ color: 'var(--text-primary)' }} className="text-[28px] font-bold leading-tight">
          {value}
        </span>
        {unit && (
          <span style={{ color: 'var(--text-muted)' }} className="text-sm">
            {unit}
          </span>
        )}
      </div>
      {quality && timestamp && (
        <div className="mt-1">
          <DataQualityBadge quality={quality} timestamp={timestamp} />
        </div>
      )}
      {trend && trendLabel && (
        <div className="flex items-center gap-1 mt-1">
          {trendIcon[trend]}
          <span style={{ color: 'var(--text-muted)' }} className="text-xs">
            {trendLabel}
          </span>
        </div>
      )}
    </div>
  );
}
