import { useSearchParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { getAssets } from "@/lib/api";
import { useWorkspace } from "@/lib/WorkspaceContext";

export function AssetFilters() {
  const [searchParams, setSearchParams] = useSearchParams();
  const { plantId } = useWorkspace();

  const { data: assets } = useQuery({
    queryKey: ["assets", plantId],
    queryFn: () => getAssets({ plant_id: plantId }),
  });

  // Extract unique area_ids from current workspace assets
  const areas = [...new Set((assets || []).map((a: any) => a.area_id).filter(Boolean))];

  const setFilter = (key: string, value: string) => {
    if (value) searchParams.set(key, value);
    else searchParams.delete(key);
    setSearchParams(searchParams);
  };

  return (
    <div className="flex gap-3">
      <select
        className="bg-gray-900 border border-gray-700 rounded px-3 py-1.5 text-sm"
        onChange={(e) => setFilter("asset_type", e.target.value)}
        value={searchParams.get("asset_type") || ""}
      >
        <option value="">All Types</option>
        <option value="pump">Pump</option>
        <option value="motor">Motor</option>
        <option value="compressor_train">Compressor Train</option>
        <option value="compressor">Compressor</option>
        <option value="bearing_assembly">Bearing Assembly</option>
        <option value="lubrication_system">Lube System</option>
        <option value="cooling_system">Cooling System</option>
        <option value="seal_system">Seal System</option>
        <option value="tank">Tank</option>
        <option value="valve">Valve</option>
        <option value="transformer">Transformer</option>
        <option value="feeder">Feeder</option>
        <option value="breaker">Breaker</option>
      </select>
      <select
        className="bg-gray-900 border border-gray-700 rounded px-3 py-1.5 text-sm"
        onChange={(e) => setFilter("area_id", e.target.value)}
        value={searchParams.get("area_id") || ""}
      >
        <option value="">All Areas</option>
        {areas.map((area) => (
          <option key={area} value={area}>{area}</option>
        ))}
      </select>
    </div>
  );
}
