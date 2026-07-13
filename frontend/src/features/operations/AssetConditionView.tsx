import { useQuery } from "@tanstack/react-query";
import { fetchAPI } from "@/lib/api";
import { useWorkspace } from "@/lib/WorkspaceContext";
import { useConditionConfig } from "./hooks/useProcessConfig";
import { useAssetSignals } from "./hooks/useAssetSignals";
import { ConditionScoreCard } from "./components/ConditionScoreCard";
import { KeySignalsCard } from "./components/KeySignalsCard";
import { AlarmTimeline } from "./components/AlarmTimeline";
import { TrendBundle } from "@/components/industrial/TrendBundle";

const TREND_COLORS = ["#3b82f6", "#22c55e", "#f59e0b", "#8b5cf6", "#ef4444"];

export function AssetConditionView({ assetId }: { assetId: string }) {
  const { plantId } = useWorkspace();

  const { data: asset } = useQuery({
    queryKey: ["asset", assetId],
    queryFn: () => fetchAPI<any>(`/api/v1/assets/${assetId}`),
  });

  const { data: condConfig } = useConditionConfig(assetId);
  const { data: apiSignals = [] } = useAssetSignals(assetId);

  // Use API config if available, else fallback to asset signals from API
  const signalConfigs = condConfig?.signals?.length
    ? condConfig.signals.map((s: any) => ({ signalId: s.signal_id, label: s.label, unit: s.unit }))
    : apiSignals;
  const signalIds = signalConfigs.map((s) => s.signalId);

  const trendSignals = signalConfigs.map((s, i) => ({
    signalId: s.signalId,
    label: s.label,
    color: TREND_COLORS[i % TREND_COLORS.length],
    unit: s.unit,
  }));

  const title = asset?.name || assetId;
  const typeBadge = asset?.asset_type || "";
  const roleBadge = asset?.asset_role || "";
  const areaId = asset?.area_id || "";

  return (
    <div className="p-6 overflow-auto h-full">
      {/* Asset Header */}
      <div className="mb-4">
        <h2 className="text-xl font-bold" style={{ color: 'var(--text-primary)' }}>{title}</h2>
        <div className="flex gap-2 mt-1">
          {typeBadge && (
            <span className="text-[10px] px-1.5 py-0.5 rounded" style={{ backgroundColor: 'var(--surface-hover)', color: 'var(--text-muted)' }}>
              {typeBadge}
            </span>
          )}
          {roleBadge && (
            <span className="text-[10px] px-1.5 py-0.5 rounded" style={{ backgroundColor: 'var(--surface-hover)', color: 'var(--text-muted)' }}>
              {roleBadge}
            </span>
          )}
          {areaId && (
            <span className="text-[10px] px-1.5 py-0.5 rounded" style={{ backgroundColor: 'var(--surface-hover)', color: 'var(--text-muted)' }}>
              {areaId}
            </span>
          )}
        </div>
      </div>

      {/* Two-column layout */}
      <div className="grid grid-cols-2 gap-4">
        {/* Left: Condition Score + Key Signals */}
        <div className="space-y-4">
          <ConditionScoreCard assetId={assetId} signalIds={signalIds} />
          <KeySignalsCard signalConfigs={signalConfigs} />
        </div>

        {/* Right: Trend Bundle */}
        <div>
          {trendSignals.length > 0 ? (
            <TrendBundle
              title="Signal Trends"
              signals={trendSignals}
              height={320}
              defaultTimeRange="30m"
            />
          ) : (
            <div
              className="rounded-lg border p-4 flex items-center justify-center h-64"
              style={{ backgroundColor: 'var(--surface-card)', borderColor: 'var(--border-default)', color: 'var(--text-muted)' }}
            >
              <span className="text-sm">No signals configured</span>
            </div>
          )}
        </div>
      </div>

      {/* Bottom: Alarm Timeline */}
      <div className="mt-4">
        <AlarmTimeline assetId={assetId} />
      </div>
    </div>
  );
}