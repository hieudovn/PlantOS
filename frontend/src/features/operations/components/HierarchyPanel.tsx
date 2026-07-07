import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { ChevronRight, ChevronDown, Building2, Wrench } from "lucide-react";
import { useWorkspace } from "@/lib/WorkspaceContext";
import { fetchAPI } from "@/lib/api";

interface Props {
  onSelect: (obj: { type: string; id: string } | null) => void;
  selectedId?: string;
}

export function HierarchyPanel({ onSelect, selectedId }: Props) {
  const { plantId } = useWorkspace();
  const navigate = useNavigate();
  const [expandedAreas, setExpandedAreas] = useState<Set<string>>(new Set());

  const { data: areas } = useQuery({
    queryKey: ["areas", plantId],
    queryFn: () => fetchAPI<any[]>(`/api/v1/areas?plant_id=${plantId}`),
  });

  const { data: assets } = useQuery({
    queryKey: ["assets", plantId],
    queryFn: () => fetchAPI<any[]>(`/api/v1/assets?plant_id=${plantId}`),
  });

  const toggleArea = (areaId: string) => {
    setExpandedAreas((prev) => {
      const next = new Set(prev);
      if (next.has(areaId)) next.delete(areaId);
      else next.add(areaId);
      return next;
    });
  };

  const handleSelectPlant = () => {
    onSelect(null);
    navigate("/operations");
  };

  const handleSelectArea = (areaId: string) => {
    onSelect({ type: "area", id: areaId });
    toggleArea(areaId);
    navigate(`/operations/area/${areaId}`);
  };

  const handleSelectAsset = (assetId: string) => {
    onSelect({ type: "asset", id: assetId });
    navigate(`/operations/asset/${assetId}`);
  };

  const assetsByArea: Record<string, any[]> = {};
  (assets || []).forEach((a: any) => {
    const key = a.area_id || "__no_area";
    if (!assetsByArea[key]) assetsByArea[key] = [];
    assetsByArea[key].push(a);
  });

  return (
    <div
      className="w-60 overflow-y-auto border-r shrink-0"
      style={{ backgroundColor: 'var(--surface-primary)', borderColor: 'var(--border-default)' }}
    >
      {/* Plant root */}
      <div
        onClick={handleSelectPlant}
        className="flex items-center gap-2 px-3 py-2 text-sm cursor-pointer transition-colors"
        style={{
          backgroundColor: !selectedId ? 'var(--surface-hover)' : 'transparent',
          color: !selectedId ? 'var(--text-primary)' : 'var(--text-secondary)',
        }}
        onMouseEnter={(e) => { if (selectedId) e.currentTarget.style.backgroundColor = 'var(--surface-hover)'; }}
        onMouseLeave={(e) => { if (selectedId) e.currentTarget.style.backgroundColor = 'transparent'; }}
      >
        <Building2 className="w-4 h-4" />
        <span className="font-medium">{plantId}</span>
      </div>

      {/* Areas */}
      {(areas || []).map((area: any) => {
        const isExpanded = expandedAreas.has(area.area_id);
        const isSelected = selectedId === area.area_id;
        const areaAssets = assetsByArea[area.area_id] || [];
        return (
          <div key={area.area_id}>
            <div
              onClick={() => handleSelectArea(area.area_id)}
              className="flex items-center gap-1 px-3 py-1.5 text-sm cursor-pointer transition-colors pl-6"
              style={{
                backgroundColor: isSelected ? 'var(--surface-hover)' : 'transparent',
                color: isSelected ? 'var(--text-primary)' : 'var(--text-secondary)',
              }}
              onMouseEnter={(e) => { if (!isSelected) e.currentTarget.style.backgroundColor = 'var(--surface-hover)'; }}
              onMouseLeave={(e) => { if (!isSelected) e.currentTarget.style.backgroundColor = 'transparent'; }}
            >
              {isExpanded ? <ChevronDown className="w-3 h-3 shrink-0" /> : <ChevronRight className="w-3 h-3 shrink-0" />}
              <span className="truncate">{area.name || area.area_id}</span>
            </div>

            {/* Assets under this area */}
            {isExpanded && areaAssets.map((asset: any) => {
              const isAssetSelected = selectedId === asset.asset_id;
              return (
                <div
                  key={asset.asset_id}
                  onClick={() => handleSelectAsset(asset.asset_id)}
                  className="flex items-center gap-2 px-3 py-1 text-sm cursor-pointer transition-colors pl-10"
                  style={{
                    backgroundColor: isAssetSelected ? 'var(--surface-hover)' : 'transparent',
                    color: isAssetSelected ? 'var(--text-primary)' : 'var(--text-secondary)',
                  }}
                  onMouseEnter={(e) => { if (!isAssetSelected) e.currentTarget.style.backgroundColor = 'var(--surface-hover)'; }}
                  onMouseLeave={(e) => { if (!isAssetSelected) e.currentTarget.style.backgroundColor = 'transparent'; }}
                >
                  <Wrench className="w-3 h-3 shrink-0" />
                  <span className="truncate">{asset.name || asset.asset_id}</span>
                </div>
              );
            })}
          </div>
        );
      })}
    </div>
  );
}
