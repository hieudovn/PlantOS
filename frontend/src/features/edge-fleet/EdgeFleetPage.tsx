import { useQuery } from "@tanstack/react-query";
import { StatusBadge } from "@/components/StatusBadge";

async function getEdgeNodes() {
  const res = await fetch("/api/v1/edge-nodes");
  if (!res.ok) throw new Error("Failed");
  return res.json();
}

export function EdgeFleetPage() {
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
                <th className="text-left px-4 py-3">Status</th>
                <th className="text-left px-4 py-3">Backlog</th>
                <th className="text-left px-4 py-3">Last Heartbeat</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800">
              {nodes?.map((n: any) => (
                <tr key={n.edge_node_id}>
                  <td className="px-4 py-3 font-mono text-xs">{n.edge_node_id}</td>
                  <td className="px-4 py-3">
                    <StatusBadge status={n.status} />
                  </td>
                  <td className="px-4 py-3 text-gray-400">{n.backlog_count}</td>
                  <td className="px-4 py-3 text-gray-500 text-xs">
                    {n.last_heartbeat
                      ? new Date(n.last_heartbeat).toLocaleString()
                      : "—"}
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
