import { useQuery } from "@tanstack/react-query";
import { X, Building2, Wrench } from "lucide-react";
import { fetchAPI } from "@/lib/api";

interface Props {
  object: { type: string; id: string } | null;
  onClose: () => void;
}

export function ContextPanel({ object, onClose }: Props) {
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
        <span className="text-sm font-medium" style={{ color: 'var(--text-primary)' }}>
          {object ? (entity?.name || object.id) : "Details"}
        </span>
        <button
          onClick={onClose}
          className="p-1 rounded hover:opacity-80 transition-opacity"
          style={{ color: 'var(--text-muted)' }}
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Content */}
      <div className="p-4">
        {object ? (
          <div className="space-y-4">
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

            {/* Object Name */}
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

            {/* Placeholder */}
            <div
              className="mt-6 p-3 rounded text-xs"
              style={{ backgroundColor: 'var(--surface-secondary)', color: 'var(--text-muted)' }}
            >
              KPIs and trends will appear here in Phase 6-PV-04.
            </div>
          </div>
        ) : (
          <div className="flex items-center justify-center h-32 text-xs" style={{ color: 'var(--text-muted)' }}>
            Select an area or asset to view details
          </div>
        )}
      </div>
    </div>
  );
}
