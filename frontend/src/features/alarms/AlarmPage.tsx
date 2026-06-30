import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { StatusBadge } from "@/components/StatusBadge";

const severityColors: Record<string, string> = {
  low: "bg-blue-500/20 text-blue-400",
  medium: "bg-yellow-500/20 text-yellow-400",
  high: "bg-orange-500/20 text-orange-400",
  critical: "bg-red-500/20 text-red-400",
};

async function getAlarms(params?: Record<string, string>) {
  const qs = params ? "?" + new URLSearchParams(params).toString() : "";
  const res = await fetch(`/api/v1/alarms${qs}`);
  if (!res.ok) throw new Error("Failed");
  return res.json();
}

async function ackAlarm(alarmId: string) {
  const res = await fetch(`/api/v1/alarms/${alarmId}/ack`, { method: "PATCH" });
  if (!res.ok) throw new Error("Failed");
  return res.json();
}

export function AlarmPage() {
  const [stateFilter, setStateFilter] = useState("");

  const { data: alarms, isLoading, refetch } = useQuery({
    queryKey: ["alarms", { state: stateFilter }],
    queryFn: () => getAlarms(stateFilter ? { state: stateFilter } : undefined),
    refetchInterval: 5000,
  });

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Alarms</h1>
        <div className="flex items-center gap-2">
          <select
            value={stateFilter}
            onChange={e => setStateFilter(e.target.value)}
            className="bg-gray-900 border border-gray-700 rounded px-3 py-1.5 text-sm"
          >
            <option value="">All States</option>
            <option value="active">Active</option>
            <option value="acknowledged">Acknowledged</option>
            <option value="cleared">Cleared</option>
          </select>
          <span className="text-sm text-gray-500">{alarms?.length || 0} alarms</span>
        </div>
      </div>

      {isLoading ? (
        <div className="text-gray-500">Loading...</div>
      ) : (
        <div className="rounded-lg border border-gray-800 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-900 text-gray-400">
              <tr>
                <th className="text-left px-4 py-3">Alarm ID</th>
                <th className="text-left px-4 py-3">Signal</th>
                <th className="text-left px-4 py-3">Severity</th>
                <th className="text-left px-4 py-3">State</th>
                <th className="text-left px-4 py-3">Message</th>
                <th className="text-left px-4 py-3">Value</th>
                <th className="text-left px-4 py-3">Time</th>
                <th className="text-left px-4 py-3">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800">
              {alarms?.map((a: any) => (
                <tr key={a.alarm_id} className="hover:bg-gray-800/50">
                  <td className="px-4 py-3 font-mono text-xs">{a.alarm_id}</td>
                  <td className="px-4 py-3 font-mono text-xs">{a.signal_id}</td>
                  <td className="px-4 py-3">
                    <span
                      className={`inline-flex px-2 py-0.5 rounded text-xs font-medium ${
                        severityColors[a.severity] || ""
                      }`}
                    >
                      {a.severity}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <StatusBadge status={a.state} />
                  </td>
                  <td className="px-4 py-3 text-gray-300">{a.message || "—"}</td>
                  <td className="px-4 py-3 text-gray-400">
                    {a.trigger_value != null ? a.trigger_value : "—"}
                  </td>
                  <td className="px-4 py-3 text-gray-500 text-xs">
                    {new Date(a.started_at).toLocaleString()}
                  </td>
                  <td className="px-4 py-3">
                    {a.state === "active" && (
                      <button
                        onClick={async () => {
                          await ackAlarm(a.alarm_id);
                          refetch();
                        }}
                        className="px-2 py-1 bg-gray-700 hover:bg-gray-600 rounded text-xs"
                      >
                        Ack
                      </button>
                    )}
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
