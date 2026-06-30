import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { StatusBadge } from "@/components/StatusBadge";

async function getEdgeNodes() {
  const res = await fetch("/api/v1/edge-nodes");
  if (!res.ok) throw new Error("Failed");
  return res.json();
}

function EdgeNodeDetail({ nodeId }: { nodeId: string }) {
  const { data: status } = useQuery({
    queryKey: ["edge-status", nodeId],
    queryFn: () => fetch(`http://localhost:8001/api/status`).then(r => r.json()),
    refetchInterval: 5000,
  });

  if (!status) return <div className="text-gray-500 text-sm">Loading...</div>;

  return (
    <div className="space-y-3 text-sm">
      <div>
        <span className="text-gray-500">Uptime:</span>{" "}
        {Math.floor(status.uptime_seconds / 60)}m
      </div>
      <div>
        <span className="text-gray-500">DB Rows:</span>{" "}
        {status.duckdb.total_rows}
      </div>
      <div>
        <span className="text-gray-500">Unsynced:</span>{" "}
        <span
          className={
            status.duckdb.unsynced > 0 ? "text-yellow-400" : "text-green-400"
          }
        >
          {status.duckdb.unsynced}
        </span>
      </div>
      <div>
        <span className="text-gray-500">MQTT:</span>{" "}
        <span
          className={
            status.mqtt.connected ? "text-green-400" : "text-red-400"
          }
        >
          {status.mqtt.connected ? "Connected" : "Disconnected"}
        </span>
      </div>
      <div>
        <span className="text-gray-500">Signals:</span> {status.signals}
      </div>
      <div>
        <span className="text-gray-500">DB Size:</span>{" "}
        {status.duckdb.db_size_mb} MB
      </div>
      <a
        href="http://localhost:8001"
        target="_blank"
        rel="noopener noreferrer"
        className="text-blue-400 text-xs hover:underline"
      >
        Open Edge Dashboard &rarr;
      </a>
    </div>
  );
}

export function EdgeFleetPage() {
  const [selectedNode, setSelectedNode] = useState<string | null>(null);

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
                  <th className="text-left px-4 py-3">Status</th>
                  <th className="text-left px-4 py-3">Backlog</th>
                  <th className="text-left px-4 py-3">Last Heartbeat</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-800">
                {nodes?.map((n: any) => (
                  <tr
                    key={n.edge_node_id}
                    onClick={() => setSelectedNode(n.edge_node_id)}
                    className={`cursor-pointer transition-colors hover:bg-gray-800/50 ${
                      selectedNode === n.edge_node_id ? "bg-gray-800" : ""
                    }`}
                  >
                    <td className="px-4 py-3 font-mono text-xs">
                      {n.edge_node_id}
                    </td>
                    <td className="px-4 py-3">
                      <StatusBadge status={n.status} />
                    </td>
                    <td className="px-4 py-3 text-gray-400">
                      {n.backlog_count}
                    </td>
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
          {selectedNode && (
            <div className="w-80 bg-gray-900 border border-gray-800 rounded-lg p-4 space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="font-bold text-sm">{selectedNode}</h3>
                <button
                  onClick={() => setSelectedNode(null)}
                  className="text-gray-500 hover:text-white text-xs"
                >
                  &times;
                </button>
              </div>
              <EdgeNodeDetail nodeId={selectedNode} />
            </div>
          )}
        </div>
      )}
    </div>
  );
}
