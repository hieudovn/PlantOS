import { useSearchParams } from "react-router-dom";

export function AssetFilters() {
  const [searchParams, setSearchParams] = useSearchParams();

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
        <option value="PROCESS-AREA">Process Area</option>
        <option value="ELECTRICAL-AREA">Electrical Area</option>
      </select>
    </div>
  );
}
