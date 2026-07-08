import { useParams, useNavigate, Link } from "react-router-dom";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { getAsset, getSignals, deleteAsset } from "@/lib/api";
import { StatusBadge } from "@/components/StatusBadge";
import { useRealtimeValues } from "@/lib/useRealtimeValues";
import { Trash2 } from "lucide-react";

export function AssetDetail() {
  const { assetId } = useParams<{ assetId: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const { data: asset } = useQuery({
    queryKey: ["asset", assetId],
    queryFn: () => getAsset(assetId!),
    enabled: !!assetId,
  });

  const { data: signals } = useQuery({
    queryKey: ["signals", assetId],
    queryFn: () => getSignals({ asset_id: assetId! }),
    enabled: !!assetId,
  });

  const currentValues = useRealtimeValues(assetId ? [assetId] : []);

  async function handleDelete() {
    if (!confirm(`Delete asset "${assetId}"? This will soft-delete it.`)) return;
    try {
      await deleteAsset(assetId!);
      queryClient.invalidateQueries({ queryKey: ["assets"] });
      navigate("/assets");
    } catch (err: any) {
      alert(err.message || "Delete failed");
    }
  }

  if (!asset) return <div className="text-gray-500">Loading...</div>;

  return (
    <div className="space-y-6 max-w-4xl">
      <div className="flex items-center gap-4">
        <Link to="/assets" className="text-gray-500 hover:text-white text-sm">← Assets</Link>
        <h1 className="text-2xl font-bold">{asset.name}</h1>
        <StatusBadge status={asset.lifecycle_status} />
        <button
          onClick={handleDelete}
          className="ml-auto p-1.5 rounded hover:bg-gray-800"
          title="Delete asset"
        >
          <Trash2 className="w-4 h-4" style={{ color: '#ef4444' }} />
        </button>
      </div>

      {/* Metadata */}
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-gray-900 rounded-lg p-4 border border-gray-800">
          <div className="text-xs text-gray-500">Asset ID</div>
          <div className="font-mono text-sm mt-1">{asset.asset_id}</div>
        </div>
        <div className="bg-gray-900 rounded-lg p-4 border border-gray-800">
          <div className="text-xs text-gray-500">Type</div>
          <div className="text-sm mt-1 capitalize">{asset.asset_type}</div>
        </div>
        <div className="bg-gray-900 rounded-lg p-4 border border-gray-800">
          <div className="text-xs text-gray-500">Role</div>
          <div className="text-sm mt-1">
            <span className="text-xs px-1.5 py-0.5 rounded" style={{ backgroundColor: 'var(--surface-hover)' }}>
              {asset.asset_role}
            </span>
          </div>
        </div>
        <div className="bg-gray-900 rounded-lg p-4 border border-gray-800">
          <div className="text-xs text-gray-500">Area</div>
          <div className="text-sm mt-1">{asset.area_id || "—"}</div>
        </div>
      </div>

      {/* Current Values */}
      <div>
        <h2 className="text-lg font-semibold mb-3">Current Values</h2>
        <div className="rounded-lg border border-gray-800 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-900 text-gray-400">
              <tr>
                <th className="text-left px-4 py-2">Signal</th>
                <th className="text-right px-4 py-2">Value</th>
                <th className="text-left px-4 py-2">Quality</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800">
              {signals?.map((s: any) => {
                const cv = currentValues[s.signal_id];
                return (
                  <tr key={s.signal_id}>
                    <td className="px-4 py-2 font-mono text-xs">{s.signal_name}</td>
                    <td className="px-4 py-2 text-right">
                      {cv ? (
                        <span>
                          {cv.value} {s.engineering_unit && <span className="text-gray-500">{s.engineering_unit}</span>}
                        </span>
                      ) : (
                        <span className="text-gray-600">—</span>
                      )}
                    </td>
                    <td className="px-4 py-2">
                      {cv && <StatusBadge status={cv.quality?.toLowerCase()} />}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Signals List */}
      <div>
        <h2 className="text-lg font-semibold mb-3">Signals ({signals?.length || 0})</h2>
        <div className="rounded-lg border border-gray-800 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-900 text-gray-400">
              <tr>
                <th className="text-left px-4 py-2">Signal ID</th>
                <th className="text-left px-4 py-2">Name</th>
                <th className="text-left px-4 py-2">Type</th>
                <th className="text-left px-4 py-2">Unit</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800">
              {signals?.map((s: any) => (
                <tr key={s.signal_id} className="hover:bg-gray-800/50">
                  <td className="px-4 py-2 font-mono text-xs">{s.signal_id}</td>
                  <td className="px-4 py-2">{s.display_name || s.signal_name}</td>
                  <td className="px-4 py-2 text-gray-400">{s.data_type}</td>
                  <td className="px-4 py-2 text-gray-400">{s.engineering_unit || "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
