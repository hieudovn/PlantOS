import { useQuery } from "@tanstack/react-query";
import { useNavigate, useSearchParams } from "react-router-dom";
import { getAssets } from "@/lib/api";
import { StatusBadge } from "@/components/StatusBadge";
import { AssetFilters } from "./AssetFilters";

export function AssetTable() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  const params: Record<string, string> = {};
  searchParams.forEach((v, k) => { params[k] = v; });

  const { data: assets, isLoading } = useQuery({
    queryKey: ["assets", params],
    queryFn: () => getAssets(params),
  });

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Assets</h1>
        <span className="text-sm text-gray-500">{assets?.length || 0} assets</span>
      </div>

      <AssetFilters />

      {isLoading ? (
        <div className="text-gray-500">Loading...</div>
      ) : (
        <div className="rounded-lg border border-gray-800 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-900 text-gray-400">
              <tr>
                <th className="text-left px-4 py-3">Asset ID</th>
                <th className="text-left px-4 py-3">Name</th>
                <th className="text-left px-4 py-3">Type</th>
                <th className="text-left px-4 py-3">Area</th>
                <th className="text-left px-4 py-3">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800">
              {assets?.map((a: any) => (
                <tr
                  key={a.asset_id}
                  className="hover:bg-gray-800/50 cursor-pointer transition-colors"
                  onClick={() => navigate(`/assets/${a.asset_id}`)}
                >
                  <td className="px-4 py-3 font-mono text-xs">{a.asset_id}</td>
                  <td className="px-4 py-3">{a.name}</td>
                  <td className="px-4 py-3 text-gray-400">{a.asset_type}</td>
                  <td className="px-4 py-3 text-gray-400">{a.area_id || "—"}</td>
                  <td className="px-4 py-3">
                    <StatusBadge status={a.lifecycle_status} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
