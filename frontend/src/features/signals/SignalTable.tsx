import { useQuery } from "@tanstack/react-query";
import { useSearchParams } from "react-router-dom";
import { getSignals } from "@/lib/api";

export function SignalTable() {
  const [searchParams] = useSearchParams();
  const params: Record<string, string> = {};
  searchParams.forEach((v, k) => { params[k] = v; });

  const { data: signals, isLoading } = useQuery({
    queryKey: ["signals-all", params],
    queryFn: () => getSignals(params),
  });

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Signals</h1>
        <span className="text-sm text-gray-500">{signals?.length || 0} signals</span>
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
                <th className="text-left px-4 py-3">UNS Path</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800">
              {signals?.map((s: any) => (
                <tr key={s.signal_id} className="hover:bg-gray-800/50">
                  <td className="px-4 py-3 font-mono text-xs">{s.signal_id}</td>
                  <td className="px-4 py-3">{s.display_name || s.signal_name}</td>
                  <td className="px-4 py-3 text-gray-400">{s.asset_id}</td>
                  <td className="px-4 py-3 text-gray-400">{s.data_type}</td>
                  <td className="px-4 py-3 text-gray-400">{s.engineering_unit || "—"}</td>
                  <td className="px-4 py-3 font-mono text-xs text-gray-500">{s.uns_path || "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
