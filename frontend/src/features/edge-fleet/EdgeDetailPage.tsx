import { useParams, useNavigate } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { StatusBadge } from "@/components/StatusBadge";
import {
  getEdgeNode,
  getEdgeConnectors,
  getEdgeHeartbeats,
  getEdgeCommands,
  createEdgeCommand,
} from "@/lib/api";
import { useState } from "react";

export function EdgeDetailPage() {
  const { edgeNodeId } = useParams<{ edgeNodeId: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [actionMsg, setActionMsg] = useState("");

  const { data: node, isLoading: nodeLoading } = useQuery({
    queryKey: ["edge-node", edgeNodeId],
    queryFn: () => getEdgeNode(edgeNodeId!),
    enabled: !!edgeNodeId,
    refetchInterval: 10000,
  });

  const { data: connectors } = useQuery({
    queryKey: ["edge-connectors", edgeNodeId],
    queryFn: () => getEdgeConnectors(edgeNodeId!),
    enabled: !!edgeNodeId,
    refetchInterval: 15000,
  });

  const { data: heartbeats } = useQuery({
    queryKey: ["edge-heartbeats", edgeNodeId],
    queryFn: () => getEdgeHeartbeats(edgeNodeId!),
    enabled: !!edgeNodeId,
  });

  const { data: commands } = useQuery({
    queryKey: ["edge-commands", edgeNodeId],
    queryFn: () => getEdgeCommands(edgeNodeId!),
    enabled: !!edgeNodeId,
    refetchInterval: 10000,
  });

  const cmdMutation = useMutation({
    mutationFn: ({ type, target }: { type: string; target?: string }) =>
      createEdgeCommand(edgeNodeId!, type, target),
    onSuccess: () => {
      setActionMsg("Command sent successfully");
      queryClient.invalidateQueries({ queryKey: ["edge-commands", edgeNodeId] });
      setTimeout(() => setActionMsg(""), 3000);
    },
    onError: (err: Error) => {
      setActionMsg(`Command failed: ${err.message}`);
      setTimeout(() => setActionMsg(""), 5000);
    },
  });

  if (nodeLoading) {
    return (
      <div className="p-8">
        <div className="text-gray-500">Loading edge node details...</div>
      </div>
    );
  }

  if (!node) {
    return (
      <div className="p-8">
        <div className="text-gray-500">Edge node not found</div>
        <button className="mt-4 text-blue-400" onClick={() => navigate("/edge")}>
          ← Back to Edge Fleet
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <button className="text-blue-400 hover:text-blue-300" onClick={() => navigate("/edge")}>
          ← Fleet
        </button>
        <h1 className="text-2xl font-bold">{edgeNodeId}</h1>
        <StatusBadge status={node.status} />
      </div>

      {/* Action feedback */}
      {actionMsg && (
        <div className="bg-blue-900/30 border border-blue-700 text-blue-300 px-4 py-2 rounded text-sm">
          {actionMsg}
        </div>
      )}

      {/* Overview Card */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <OverviewCard label="Status" value={node.status} />
        <OverviewCard label="Version" value={node.version || "—"} />
        <OverviewCard label="Hostname" value={node.hostname || "—"} />
        <OverviewCard label="IP Address" value={node.ip_address || "—"} />
        <OverviewCard label="Signals" value={String(node.signal_count ?? "—")} />
        <OverviewCard label="Backlog" value={String(node.backlog_count ?? 0)} />
        <OverviewCard label="Disk" value={node.disk_usage_mb ? `${node.disk_usage_mb} MB` : "—"} />
        <OverviewCard label="Center Sync" value={node.center_sync || "—"} />
      </div>

      {/* Actions */}
      <div className="rounded-lg border border-gray-800 p-4">
        <h2 className="text-sm font-semibold mb-3 text-gray-400 uppercase tracking-wider">Actions</h2>
        <div className="flex flex-wrap gap-3">
          <button
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded text-sm font-medium transition-colors"
            onClick={() => cmdMutation.mutate({ type: "sync_now" })}
          >
            Sync Now
          </button>
          <button
            className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded text-sm font-medium transition-colors"
            onClick={() => cmdMutation.mutate({ type: "reload_config" })}
          >
            Reload Config
          </button>
          <button
            className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            disabled
            title="Available after Edge v2 packaging (E2V2-5)"
          >
            Restart Agent
            <span className="ml-2 text-xs text-gray-500">(E2V2-5)</span>
          </button>
        </div>
      </div>

      {/* Connectors */}
      <div className="rounded-lg border border-gray-800 overflow-hidden">
        <h2 className="text-sm font-semibold p-4 bg-gray-900 text-gray-400 uppercase tracking-wider border-b border-gray-800">
          Connectors
        </h2>
        <table className="w-full text-sm">
          <thead className="bg-gray-900/50 text-gray-500">
            <tr>
              <th className="text-left px-4 py-3">Connector ID</th>
              <th className="text-left px-4 py-3">Type</th>
              <th className="text-left px-4 py-3">Status</th>
              <th className="text-left px-4 py-3">Signals</th>
              <th className="text-left px-4 py-3">Last Error</th>
              <th className="text-left px-4 py-3">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-800">
            {connectors?.length ? (
              connectors.map((c: any) => (
                <tr key={c.connector_id} className="hover:bg-gray-800/30">
                  <td className="px-4 py-3 font-medium">{c.connector_id}</td>
                  <td className="px-4 py-3 text-gray-400">{c.type}</td>
                  <td className="px-4 py-3"><StatusBadge status={c.status} /></td>
                  <td className="px-4 py-3">{c.signal_count ?? 0}</td>
                  <td className="px-4 py-3 text-red-400 text-xs">{c.last_error || "—"}</td>
                  <td className="px-4 py-3">
                    <button
                      className="text-xs px-2 py-1 bg-gray-700 hover:bg-gray-600 rounded"
                      onClick={() => cmdMutation.mutate({ type: "restart_connector", target: c.connector_id })}
                    >
                      Restart
                    </button>
                  </td>
                </tr>
              ))
            ) : (
              <tr><td colSpan={6} className="px-4 py-8 text-center text-gray-500">No connector data available</td></tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Command History */}
      <div className="rounded-lg border border-gray-800 overflow-hidden">
        <h2 className="text-sm font-semibold p-4 bg-gray-900 text-gray-400 uppercase tracking-wider border-b border-gray-800">
          Command History
        </h2>
        <table className="w-full text-sm">
          <thead className="bg-gray-900/50 text-gray-500">
            <tr>
              <th className="text-left px-4 py-3">Type</th>
              <th className="text-left px-4 py-3">Target</th>
              <th className="text-left px-4 py-3">Status</th>
              <th className="text-left px-4 py-3">Result</th>
              <th className="text-left px-4 py-3">Created</th>
              <th className="text-left px-4 py-3">Finished</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-800">
            {commands?.length ? (
              commands.map((c: any) => (
                <tr key={c.command_id} className="hover:bg-gray-800/30">
                  <td className="px-4 py-3 font-medium">{c.command_type}</td>
                  <td className="px-4 py-3 text-gray-400">{c.target || "—"}</td>
                  <td className="px-4 py-3"><StatusBadge status={c.status} /></td>
                  <td className="px-4 py-3 text-xs text-gray-400">{c.result_message || "—"}</td>
                  <td className="px-4 py-3 text-xs text-gray-500">
                    {c.created_at ? new Date(c.created_at).toLocaleString() : "—"}
                  </td>
                  <td className="px-4 py-3 text-xs text-gray-500">
                    {c.finished_at ? new Date(c.finished_at).toLocaleString() : "—"}
                  </td>
                </tr>
              ))
            ) : (
              <tr><td colSpan={6} className="px-4 py-8 text-center text-gray-500">No commands yet</td></tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Recent Heartbeats */}
      <div className="rounded-lg border border-gray-800 overflow-hidden">
        <h2 className="text-sm font-semibold p-4 bg-gray-900 text-gray-400 uppercase tracking-wider border-b border-gray-800">
          Recent Heartbeats (Last 100)
        </h2>
        <div className="overflow-x-auto max-h-64 overflow-y-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-900/50 text-gray-500 sticky top-0">
              <tr>
                <th className="text-left px-4 py-3">Time</th>
                <th className="text-left px-4 py-3">Status</th>
                <th className="text-left px-4 py-3">Signals</th>
                <th className="text-left px-4 py-3">Backlog</th>
                <th className="text-left px-4 py-3">Version</th>
                <th className="text-left px-4 py-3">Disk (MB)</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800">
              {heartbeats?.length ? (
                heartbeats.map((hb: any) => (
                  <tr key={hb.id} className="hover:bg-gray-800/30">
                    <td className="px-4 py-2 text-xs text-gray-400">
                      {hb.received_at ? new Date(hb.received_at).toLocaleString() : "—"}
                    </td>
                    <td className="px-4 py-2"><StatusBadge status={hb.status} /></td>
                    <td className="px-4 py-2">{hb.signal_count ?? 0}</td>
                    <td className="px-4 py-2">{hb.backlog_count ?? 0}</td>
                    <td className="px-4 py-2 text-xs text-gray-400">{hb.edge_version || "—"}</td>
                    <td className="px-4 py-2">{hb.disk_usage_mb ?? "—"}</td>
                  </tr>
                ))
              ) : (
                <tr><td colSpan={6} className="px-4 py-8 text-center text-gray-500">No heartbeats yet</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

function OverviewCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-gray-800 p-4 bg-gray-900/30">
      <div className="text-xs text-gray-500 uppercase tracking-wider mb-1">{label}</div>
      <div className="text-lg font-semibold">{value}</div>
    </div>
  );
}
