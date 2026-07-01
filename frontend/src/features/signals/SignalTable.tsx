import { useState } from "react";
import { useQuery, useQueries } from "@tanstack/react-query";
import { useSearchParams } from "react-router-dom";
import { getAssets, getSignals, getCurrentValues } from "@/lib/api";
import { useWorkspace } from "@/lib/WorkspaceContext";
import { Search } from "lucide-react";

export function SignalTable() {
  const [searchParams] = useSearchParams();
  const params: Record<string, string> = {};
  searchParams.forEach((v, k) => { params[k] = v; });
  const [search, setSearch] = useState("");
  const { plantId } = useWorkspace();

  // Fetch assets for current workspace to filter signals by plant
  const { data: plantAssets } = useQuery({
    queryKey: ["assets", plantId],
    queryFn: () => getAssets({ plant_id: plantId }),
  });

  const { data: signals, isLoading } = useQuery({
    queryKey: ["signals-all"],
    queryFn: () => getSignals(),
  });

  // Get the set of asset_ids belonging to this plant
  const assetIds = new Set((plantAssets || []).map((a: any) => a.asset_id));

  // Filter signals: only those belonging to the current workspace's assets
  const plantSignals = (signals || []).filter((s: any) => assetIds.has(s.asset_id));

  // Fetch current values for all displayed signals in parallel
  const currentQueries = useQueries({
    queries: (plantSignals || []).map((s: any) => ({
      queryKey: ["current", plantId, s.signal_id],
      queryFn: () => getCurrentValues({ signal_id: s.signal_id }),
      enabled: !!s.signal_id && plantSignals.length > 0,
      refetchInterval: 10000,
    })),
  });

  // Build lookup: signal_id -> current value
  const currentMap: Record<string, any> = {};
  currentQueries.forEach((q, i) => {
    const sid = plantSignals[i]?.signal_id;
    if (sid && q.data) {
      const val = Array.isArray(q.data) ? q.data[0] : q.data;
      if (val) currentMap[sid] = val;
    }
  });

  // Apply search filter
  const filtered = plantSignals?.filter((s: any) =>
    !search ||
    s.signal_id.toLowerCase().includes(search.toLowerCase()) ||
    (s.display_name || s.signal_name).toLowerCase().includes(search.toLowerCase()) ||
    (s.asset_id || "").toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Signals</h1>
        <span className="text-sm text-gray-500">{filtered?.length || 0} signals</span>
      </div>

      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
        <input
          type="text"
          placeholder="Search by signal ID, name, or asset..."
          value={search}
          onChange={e => setSearch(e.target.value)}
          className="w-64 bg-gray-900 border border-gray-700 rounded pl-10 pr-3 py-2 text-sm"
        />
      </div>

      {isLoading ? (
        <div className="text-gray-500">Loading...</div>
      ) : (
        <div className="rounded-lg border border-gray-800 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-900 text-gray-400">
              <tr>
                <th className="text-left px-4 py-3">Signal ID</th>
                <th className="text-left px-4 py-3">Name</th>
                <th className="text-left px-4 py-3">Asset</th>
                <th className="text-left px-4 py-3">Type</th>
                <th className="text-left px-4 py-3">Unit</th>
                <th className="text-left px-4 py-3">Current Value</th>
                <th className="text-left px-4 py-3">UNS Path</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800">
              {filtered?.map((s: any) => {
                const cv = currentMap[s.signal_id];
                return (
                  <tr key={s.signal_id} className="hover:bg-gray-800/50">
                    <td className="px-4 py-3 font-mono text-xs">{s.signal_id}</td>
                    <td className="px-4 py-3">{s.display_name || s.signal_name}</td>
                    <td className="px-4 py-3 text-gray-400">{s.asset_id}</td>
                    <td className="px-4 py-3 text-gray-400">{s.data_type}</td>
                    <td className="px-4 py-3 text-gray-400">{s.engineering_unit || "—"}</td>
                    <td className="px-4 py-3">
                      {cv ? (
                        <span className="flex items-center gap-2">
                          <span className="font-mono text-xs">
                            {typeof cv.value === 'number' ? cv.value.toFixed(2) : String(cv.value ?? '—')}
                          </span>
                          <span className={`badge ${(cv.quality || 'good').toLowerCase()}`}>
                            {cv.quality || 'GOOD'}
                          </span>
                        </span>
                      ) : (
                        <span className="text-gray-600">—</span>
                      )}
                    </td>
                    <td className="px-4 py-3 font-mono text-xs text-gray-500">{s.uns_path || "—"}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
