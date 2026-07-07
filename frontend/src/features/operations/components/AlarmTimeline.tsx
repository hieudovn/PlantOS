import { useQuery } from "@tanstack/react-query";
import { Circle } from "lucide-react";
import { fetchAPI } from "@/lib/api";

interface Props {
  assetId: string;
}

export function AlarmTimeline({ assetId }: Props) {
  const { data: alarms } = useQuery({
    queryKey: ["alarms-timeline", assetId],
    queryFn: () => fetchAPI<any[]>(`/api/v1/alarms?asset_id=${assetId}`),
    refetchInterval: 30000,
  });

  const hasAlarms = alarms && alarms.length > 0;

  return (
    <div
      className="rounded-lg border p-4"
      style={{ backgroundColor: 'var(--surface-card)', borderColor: 'var(--border-default)' }}
    >
      <h3 className="text-sm font-semibold mb-3" style={{ color: 'var(--text-secondary)' }}>
        Alarm Timeline
      </h3>
      {hasAlarms ? (
        <div className="space-y-1.5">
          {(alarms || []).slice(0, 20).map((alarm: any, i: number) => (
            <div key={alarm.id || i} className="flex items-center gap-2 text-xs">
              <span style={{ color: 'var(--text-muted)' }} className="font-mono shrink-0">
                {alarm.timestamp ? alarm.timestamp.slice(0, 16).replace("T", " ") : "—"}
              </span>
              <Circle
                className="w-2 h-2 fill-current shrink-0"
                style={{ color: alarm.state === "active" ? 'var(--status-critical)' : 'var(--status-normal)' }}
              />
              <span style={{ color: alarm.state === "active" ? 'var(--status-critical)' : 'var(--status-normal)' }}>
                {alarm.state === "active" ? "⚠️" : "✅"}
              </span>
              <span style={{ color: 'var(--text-primary)' }}>{alarm.alarm_code || alarm.signal_id || `Alarm ${i + 1}`}</span>
              {alarm.message && (
                <span style={{ color: 'var(--text-muted)' }} className="truncate">— {alarm.message}</span>
              )}
            </div>
          ))}
          {(alarms || []).length > 20 && (
            <div className="text-xs text-center pt-1" style={{ color: 'var(--text-muted)' }}>
              +{(alarms || []).length - 20} more
            </div>
          )}
        </div>
      ) : (
        <div className="flex items-center gap-2 text-xs" style={{ color: 'var(--text-muted)' }}>
          <Circle className="w-3 h-3" style={{ color: 'var(--status-normal)' }} />
          No alarm history for this asset.
        </div>
      )}
    </div>
  );
}
