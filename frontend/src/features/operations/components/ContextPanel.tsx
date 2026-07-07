import { useQuery, useQueries } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { X, Building2, Wrench, ExternalLink, Circle } from "lucide-react";
import { fetchAPI, getCurrentValues } from "@/lib/api";
import { useWorkspace } from "@/lib/WorkspaceContext";
import { getAssetSignals, getThreshold } from "../config";

interface Props {
  object: { type: string; id: string } | null;
  onClose: () => void;
}

export function ContextPanel({ object, onClose }: Props) {
  const { plantId } = useWorkspace();
  const navigate = useNavigate();

  const { data: area } = useQuery({
    queryKey: ["area", object?.id],
    queryFn: () => fetchAPI<any>(`/api/v1/areas/${object?.id}`),
    enabled: object?.type === "area" && !!object?.id,
  });

  const { data: asset } = useQuery({
    queryKey: ["asset", object?.id],
    queryFn: () => fetchAPI<any>(`/api/v1/assets/${object?.id}`),
    enabled: object?.type === "asset" && !!object?.id,
  });

  const entity = area || asset;
  const typeLabel = object?.type === "area" ? "Area" : object?.type === "asset" ? "Asset" : "";

  // For assets: fetch condition score
  const signalConfigs = object?.type === "asset" ? getAssetSignals(plantId, object.id) : [];
  const signalIds = signalConfigs.map((s) => s.signalId);

  const signalQueries = useQueries({
    queries: signalIds.map((sid) => ({
      queryKey: ["current-ctx", sid],
      queryFn: () =>
        getCurrentValues({ signal_id: sid }).then((res: any) => {
          const arr = Array.isArray(res) ? res : [];
          return arr.length > 0 ? arr[0] : null;
        }),
      refetchInterval: 15000,
      enabled: signalIds.length > 0,
    })),
  });

  const signalValues = signalConfigs.map((sc, i) => ({
    ...sc,
    value: signalQueries[i]?.data?.value,
  }));

  // Compute condition score
  const statuses = signalValues.map((sv) => {
    const threshold = getThreshold(plantId, sv.signalId);
    if (!threshold || sv.value === null || sv.value === undefined) return "normal";
    if (threshold.direction === "high") {
      if (sv.value >= threshold.crit) return "critical";
      if (sv.value >= threshold.warn) return "warning";
    } else {
      if (sv.value <= threshold.crit) return "critical";
      if (sv.value <= threshold.warn) return "warning";
    }
    return "normal";
  });
  const warnCount = statuses.filter((s) => s === "warning").length;
  const critCount = statuses.filter((s) => s === "critical").length;

  return (
    <div
      className="w-80 border-l flex flex-col shrink-0 overflow-y-auto"
      style={{ backgroundColor: 'var(--surface-card)', borderColor: 'var(--border-default)' }}
    >
      {/* Header */}
      <div
        className="h-10 flex items-center justify-between px-3 border-b shrink-0"
        style={{ borderColor: 'var(--border-default)' }}
      >
        <span className="text-sm font-medium truncate" style={{ color: 'var(--text-primary)' }}>
          {object ? (entity?.name || object.id) : "Details"}
        </span>
        <button
          onClick={onClose}
          className="p-1 rounded hover:opacity-80 transition-opacity shrink-0"
          style={{ color: 'var(--text-muted)' }}
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Content */}
      <div className="p-4 space-y-4">
        {object ? (
          <>
            {/* Type badge */}
            <div
              className="inline-flex items-center gap-1.5 px-2 py-1 rounded text-xs font-medium"
              style={{ backgroundColor: 'var(--surface-hover)', color: 'var(--text-secondary)' }}
            >
              {object.type === "area" ? <Building2 className="w-3 h-3" /> : <Wrench className="w-3 h-3" />}
              {typeLabel}
            </div>

            {/* Object ID */}
            <div>
              <div className="text-xs" style={{ color: 'var(--text-muted)' }}>ID</div>
              <div className="text-sm font-mono" style={{ color: 'var(--text-primary)' }}>{object.id}</div>
            </div>

            {/* Name */}
            {entity?.name && (
              <div>
                <div className="text-xs" style={{ color: 'var(--text-muted)' }}>Name</div>
                <div className="text-sm" style={{ color: 'var(--text-primary)' }}>{entity.name}</div>
              </div>
            )}

            {/* Status */}
            {entity?.status && (
              <div>
                <div className="text-xs" style={{ color: 'var(--text-muted)' }}>Status</div>
                <div className="text-sm capitalize" style={{ color: 'var(--status-normal)' }}>{entity.status}</div>
              </div>
            )}

            {/* Asset: Condition Summary */}
            {object.type === "asset" && signalConfigs.length > 0 && (
              <div
                className="p-3 rounded text-xs space-y-2"
                style={{ backgroundColor: 'var(--surface-secondary)' }}
              >
                <div className="flex items-center justify-between">
                  <span style={{ color: 'var(--text-muted)' }}>Condition</span>
                  <span
                    className="font-bold"
                    style={{ color: critCount > 0 ? 'var(--status-critical)' : warnCount > 0 ? 'var(--status-warning)' : 'var(--status-normal)' }}
                  >
                    {critCount > 0 ? "Critical" : warnCount > 0 ? "Warning" : "Normal"}
                  </span>
                </div>
                {signalValues.map((sv) => {
                  const threshold = getThreshold(plantId, sv.signalId);
                  const st = threshold ? statuses[signalConfigs.indexOf(sv)] : "normal";
                  const sc = st === "critical" ? 'var(--status-critical)' : st === "warning" ? 'var(--status-warning)' : 'var(--status-normal)';
                  return (
                    <div key={sv.signalId} className="flex items-center justify-between">
                      <span style={{ color: 'var(--text-muted)' }}>{sv.label}</span>
                      <div className="flex items-center gap-1.5">
                        <span style={{ color: 'var(--text-primary)' }}>
                          {sv.value !== null && sv.value !== undefined ? sv.value.toFixed(1) : "—"}{sv.unit ? ` ${sv.unit}` : ""}
                        </span>
                        <Circle className="w-2 h-2 fill-current" style={{ color: sc }} />
                      </div>
                    </div>
                  );
                })}
                {/* Link to full view */}
                <button
                  onClick={() => { navigate(`/operations/asset/${object.id}`); onClose(); }}
                  className="flex items-center gap-1 mt-2 text-xs hover:underline"
                  style={{ color: 'var(--accent-primary)' }}
                >
                  <ExternalLink className="w-3 h-3" />
                  View full details
                </button>
              </div>
            )}

            {/* Area / No-config placeholder */}
            {object.type === "area" && (
              <div
                className="p-3 rounded text-xs"
                style={{ backgroundColor: 'var(--surface-secondary)', color: 'var(--text-muted)' }}
              >
                Select an asset to view condition details.
              </div>
            )}
            {object.type === "asset" && signalConfigs.length === 0 && (
              <div
                className="p-3 rounded text-xs"
                style={{ backgroundColor: 'var(--surface-secondary)', color: 'var(--text-muted)' }}
              >
                No signal configuration for this asset.
              </div>
            )}
          </>
        ) : (
          <div className="flex items-center justify-center h-32 text-xs" style={{ color: 'var(--text-muted)' }}>
            Select an area or asset to view details
          </div>
        )}
      </div>
    </div>
  );
}
