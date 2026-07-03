import { Circle } from "lucide-react";

type Props = {
  quality: string;     // "GOOD" | "UNCERTAIN" | "BAD" | "STALE" | "SIMULATED"
  timestamp?: string;  // ISO 8601
  className?: string;
};

function timeAgo(ts: string): string {
  const diff = Date.now() - new Date(ts).getTime();
  const sec = Math.floor(diff / 1000);
  if (sec < 60) return `${sec}s ago`;
  const min = Math.floor(sec / 60);
  if (min < 60) return `${min}m ago`;
  const hr = Math.floor(min / 60);
  if (hr < 24) return `${hr}h ago`;
  return `${Math.floor(hr / 24)}d ago`;
}

const qualityConfig: Record<string, { color: string; label: string }> = {
  GOOD: { color: "var(--quality-good)", label: "Good" },
  UNCERTAIN: { color: "var(--quality-uncertain)", label: "Uncertain" },
  BAD: { color: "var(--quality-bad)", label: "Bad" },
  STALE: { color: "var(--quality-stale)", label: "Stale" },
  SIMULATED: { color: "var(--status-simulated)", label: "Simulated" },
};

export function DataQualityBadge({ quality, timestamp, className = "" }: Props) {
  const cfg = qualityConfig[quality] || qualityConfig.UNCERTAIN;
  return (
    <span className={`inline-flex items-center gap-1 text-xs ${className}`}>
      <Circle className="w-2 h-2 fill-current" style={{ color: cfg.color }} />
      <span style={{ color: cfg.color }}>{cfg.label}</span>
      {timestamp && (
        <span className="text-gray-500">· {timeAgo(timestamp)}</span>
      )}
    </span>
  );
}
