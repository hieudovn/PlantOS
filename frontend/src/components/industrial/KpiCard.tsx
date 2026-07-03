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
  icon?: JSX.Element;
  compact?: boolean;
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
  label, value, unit, state, trend, trendLabel, quality, timestamp, onClick, icon, compact,
}: KpiCardProps) {
  const valSize = compact ? "text-base" : "text-xl";
  return (
    <div onClick={onClick} role={onClick ? "button" : undefined} tabIndex={onClick ? 0 : undefined}
      onKeyDown={onClick ? (e) => { if (e.key === "Enter") onClick(); } : undefined}
      style={{
        backgroundColor: 'var(--surface-card)',
        borderColor: 'var(--border-default)',
        borderLeft: state ? stateBorder[state] || undefined : undefined,
      }}
      className={`rounded-lg p-4 border ${onClick ? "cursor-pointer hover:brightness-110 transition-all" : ""}`}
    >
      <div className="flex items-center gap-2">
        {icon && <span className="flex-shrink-0">{icon}</span>}
        <div className="min-w-0 flex-1">
          <div style={{ color: 'var(--text-secondary)' }} className="text-xs mb-1">{label}</div>
          <div className="flex items-baseline gap-1">
            <span style={{ color: 'var(--text-primary)' }} className={`${valSize} font-bold leading-tight`}>{value}</span>
            {unit && <span style={{ color: 'var(--text-muted)' }} className="text-xs">{unit}</span>}
          </div>
        </div>
      </div>
      {(trend || trendLabel || quality) && (
        <div className="flex items-center gap-2 mt-2">
          {trend && trendIcon[trend]}
          {trendLabel && <span className="text-xs" style={{ color: 'var(--text-muted)' }}>{trendLabel}</span>}
          {quality && timestamp && <DataQualityBadge quality={quality} timestamp={timestamp} />}
        </div>
      )}
    </div>
  );
}
