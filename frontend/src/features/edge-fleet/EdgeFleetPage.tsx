import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { StatusBadge } from "@/components/StatusBadge";
import { getEdgeNodes } from "@/lib/api";

export function EdgeFleetPage() {
  const navigate = useNavigate();

  const { data: nodes, isLoading } = useQuery({
    queryKey: ["edge-nodes"],
    queryFn: getEdgeNodes,
    refetchInterval: 5000,
  });

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Edge Fleet</h1>
      {isLoading ? (
        <div className="text-gray-500">Loading...</div>
      ) : (
        <div className="rounded-lg border border-gray-800 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-900 text-gray-400">
              <tr>
                <th className="text-left px-4 py-3">Node ID</th>
                <th className="text-left px-4 py-3">Hostname</th>
                <th className="text-left px-4 py-3">IP</th>
                <th className="text-left px-4 py-3">Signals</th>
                <th className="text-left px-4 py-3">Status</th>
                <th className="text-left px-4 py-3">Backlog</th>
                <th className="text-left px-4 py-3">Last Heartbeat</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800">
              {nodes?.map((n: any) => (
                <tr
                  key={n.edge_node_id}
                  onClick={() => navigate(`/edge/${n.edge_node_id}`)}
                  className="cursor-pointer transition-colors hover:bg-gray-800/50"
                >
                  <td className="px-4 py-3 font-medium">{n.edge_node_id}</td>
                  <td className="px-4 py-3 text-gray-400">{n.hostname || "\u2014"}</td>
                  <td className="px-4 py-3 text-gray-400">{n.ip_address || "\u2014"}</td>
                  <td className="px-4 py-3">{n.signal_count ?? "\u2014"}</td>
                  <td className="px-4 py-3"><StatusBadge status={n.status} /></td>
                  <td className="px-4 py-3">{n.backlog_count ?? 0}</td>
                  <td className="px-4 py-3 text-gray-400">{new Date(n.last_heartbeat).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
