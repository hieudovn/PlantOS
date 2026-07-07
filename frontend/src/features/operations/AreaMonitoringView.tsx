import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { fetchAPI } from "@/lib/api";
import { AssetCard } from "./components/AssetCard";
import { PlaceholderView } from "./components/PlaceholderView";

export function AreaMonitoringView({ areaId }: { areaId: string }) {
  const navigate = useNavigate();

  const { data: assets } = useQuery({
    queryKey: ["assets-by-area", areaId],
    queryFn: () => fetchAPI<any[]>(`/api/v1/assets?area_id=${areaId}`),
  });

  const { data: area } = useQuery({
    queryKey: ["area", areaId],
    queryFn: () => fetchAPI<any>(`/api/v1/areas/${areaId}`),
    enabled: !!areaId,
  });

  // Fetch all active alarms for this area (filtered client-side by asset_id later)
  const { data: allAlarms } = useQuery({
    queryKey: ["alarms-area", areaId],
    queryFn: () => fetchAPI<any[]>("/api/v1/alarms?state=active"),
    refetchInterval: 15000,
  });

  const equipmentAssets = (assets || []).filter((a: any) => a.asset_role === "equipment");
  const areaAlarms = (allAlarms || []).filter((al: any) =>
    equipmentAssets.some((ea: any) => ea.asset_id === al.asset_id)
  ).length;

  if (!areaId) {
    return (
      <PlaceholderView
        title="Area View"
        message="Select an area from the hierarchy to begin monitoring."
      />
    );
  }

  return (
    <div className="p-6 overflow-auto h-full">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-bold" style={{ color: 'var(--text-primary)' }}>
          {area?.name || areaId}
        </h2>
        <div className="flex items-center gap-2">
          <span className="text-xs" style={{ color: 'var(--text-muted)' }}>
            {equipmentAssets.length} assets
          </span>
          {areaAlarms > 0 && (
            <span
              className="flex items-center gap-1 text-xs px-2 py-0.5 rounded"
              style={{ backgroundColor: 'rgba(234,179,8,0.15)', color: 'var(--status-warning)' }}
            >
              ⚠️ {areaAlarms} alarm{areaAlarms > 1 ? "s" : ""}
            </span>
          )}
        </div>
      </div>

      {/* Asset Cards Grid */}
      {equipmentAssets.length === 0 ? (
        <div className="flex items-center justify-center h-32 text-sm" style={{ color: 'var(--text-muted)' }}>
          No equipment assets found in this area.
        </div>
      ) : (
        <div className="grid grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {equipmentAssets.map((asset: any) => (
            <AssetCard
              key={asset.asset_id}
              asset={asset}
              onClick={() => navigate(`/operations/asset/${asset.asset_id}`)}
            />
          ))}
        </div>
      )}
    </div>
  );
}