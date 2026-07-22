import { useQueries } from "@tanstack/react-query";
import { getCurrentValues } from "@/lib/api";

type ThresholdConfig = { warn: number; crit: number; direction: "high" | "low" } | null;

interface Props {
  assetId: string;
  signalIds: string[];
}

type Status = "normal" | "warning" | "critical";

const STATUS_COLORS: Record<Status, string> = {
  normal: "var(--status-normal)",
  warning: "var(--status-warning)",
  critical: "var(--status-critical)",
};

const STATUS_LABELS: Record<Status, string> = {
  normal: "Healthy",
  warning: "Degrading",
  critical: "Critical",
};

function signalStatus(value: number | null | undefined, threshold: ThresholdConfig | null): Status {
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

function computeScore(results: Array<{ status: Status }>): number {
  if (results.length === 0) return 100;
  let normal = 0;
  let warning = 0;
  let critical = 0;
  for (const r of results) {
    if (r.status === "normal") normal++;
    else if (r.status === "warning") warning++;
    else critical++;
  }
  // Weight: normal=100, warning=50, critical=0
  const weighted = (normal * 100 + warning * 50) / results.length;
  return Math.round(Math.max(0, Math.min(100, weighted)));
}

export function ConditionScoreCard({ assetId, signalIds }: Props) {
  const { plantId } = useWorkspace();

  const queries = useQueries({
    queries: signalIds.map((sid) => ({
      queryKey: ["current-cond", sid],
      queryFn: () =>
        getCurrentValues({ signal_id: sid }).then((res: any) => {
          const arr = Array.isArray(res) ? res : [];
          return arr.length > 0 ? arr[0] : null;
        }),
      refetchInterval: 10000,
      enabled: signalIds.length > 0,
    })),
  });

  const results = signalIds.map((sid, i) => {
    const value = queries[i]?.data?.value;
    return { sid, value, status: signalStatus(value, null) };
  });

  const score = computeScore(results);
  const overallStatus: Status = score > 80 ? "normal" : score > 50 ? "warning" : "critical";

  return (
    <div
      className="rounded-lg border p-4"
      style={{ backgroundColor: 'var(--surface-card)', borderColor: 'var(--border-default)' }}
    >
      <h3 className="text-sm font-semibold mb-3" style={{ color: 'var(--text-secondary)' }}>
        Condition Score
      </h3>
      <div className="text-3xl font-bold" style={{ color: STATUS_COLORS[overallStatus] }}>
        {score}/100
      </div>
      <div
        className="text-xs mt-1 inline-flex items-center gap-1 px-2 py-0.5 rounded"
        style={{ backgroundColor: STATUS_COLORS[overallStatus] + "20", color: STATUS_COLORS[overallStatus] }}
      >
        {overallStatus === "normal" ? "✅" : overallStatus === "warning" ? "⚠️" : "🔴"} {STATUS_LABELS[overallStatus]}
      </div>
      <div className="mt-3 space-y-1">
        {results.map((r) => (
          <div key={r.sid} className="flex items-center justify-between text-xs">
            <span style={{ color: 'var(--text-muted)' }} className="truncate mr-2">{r.sid.split(".").pop()}</span>
            <span style={{ color: STATUS_COLORS[r.status] }}>
              {r.value !== null && r.value !== undefined ? r.value.toFixed(1) : "—"}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
