import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { StatusBadge } from "@/components/StatusBadge";
import { getEdgeNodes } from "@/lib/api";

export function EdgeFleetPage() {
  const [selectedNode, setSelectedNode] = useState<any | null>(null);

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
        <div className="flex gap-4">
          <div className="flex-1 rounded-lg border border-gray-800 overflow-hidden">
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
                    onClick={() => setSelectedNode(n)}
                    className={`cursor-pointer transition-colors hover:bg-gray-800/50 ${
                      selectedNode?.edge_node_id === n.edge_node_id ? "bg-gray-800" : ""
                    }`}
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
          {selectedNode && (
            <div className="w-72 rounded-lg border border-gray-800 p-4 bg-gray-900/50">
              <h2 className="text-sm font-semibold mb-3">Node Detail</h2>
              <div className="space-y-2 text-sm">
                <div><span className="text-gray-500">Node ID:</span> {selectedNode.edge_node_id}</div>
                <div><span className="text-gray-500">Hostname:</span> {selectedNode.hostname || "\u2014"}</div>
                <div><span className="text-gray-500">IP:</span> {selectedNode.ip_address || "\u2014"}</div>
                <div><span className="text-gray-500">Status:</span> <StatusBadge status={selectedNode.status} /></div>
                <div><span className="text-gray-500">Signals:</span> {selectedNode.signal_count ?? "\u2014"}</div>
                <div><span className="text-gray-500">Backlog:</span> {selectedNode.backlog_count ?? 0}</div>
                <div><span className="text-gray-500">Last Heartbeat:</span> {new Date(selectedNode.last_heartbeat).toLocaleString()}</div>
                <div><span className="text-gray-500">Version:</span> {selectedNode.version || "\u2014"}</div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
