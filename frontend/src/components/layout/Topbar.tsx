import { useState, useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { useWorkspace } from "@/lib/WorkspaceContext";
import { useNavigate } from "react-router-dom";
import { LogOut, Bell, Circle } from "lucide-react";
import { getAlarms } from "@/lib/api";

export function Topbar() {
  const { plantId, setPlantId, plants } = useWorkspace();
  const navigate = useNavigate();
  const username = localStorage.getItem("plantos_user") || "";
  const isLoggedIn = !!localStorage.getItem("plantos_token");

  const handleLogout = () => {
    localStorage.removeItem("plantos_token");
    localStorage.removeItem("plantos_user");
    navigate("/login");
  };

  // Active alarm count
  const { data: alarms } = useQuery({
    queryKey: ["alarms-active-topbar"],
    queryFn: () => getAlarms({ state: "active" }),
    refetchInterval: 15000,
  });
  const activeAlarms = (alarms || []).length;

  // Data freshness
  const [dataAge, setDataAge] = useState(0);
  useEffect(() => {
    const interval = setInterval(() => setDataAge((prev) => prev + 5), 5000);
    return () => clearInterval(interval);
  }, []);
  // Reset age on data change (simplified — resets every 5min)
  useEffect(() => {
    const reset = setInterval(() => setDataAge(0), 300000);
    return () => clearInterval(reset);
  }, []);

  const freshnessColor =
    dataAge < 30
      ? "var(--status-normal)"
      : dataAge < 120
        ? "var(--status-warning)"
        : "var(--status-critical)";

  return (
    <header style={{ backgroundColor: 'var(--surface-secondary)', borderColor: 'var(--border-default)' }} className="h-14 border-b flex items-center justify-between px-6">
      <div className="flex items-center gap-3">
        <span className="text-sm" style={{ color: 'var(--text-secondary)' }}>Workspace:</span>
        <select
          value={plantId}
          onChange={(e) => setPlantId(e.target.value)}
          className="bg-gray-800 border border-gray-700 rounded px-2 py-1 text-sm font-medium text-white focus:outline-none focus:border-blue-500"
        >
          {plants.map((p) => (
            <option key={p} value={p}>{p}</option>
          ))}
        </select>
      </div>
      <div className="flex items-center gap-3">
        {/* Data Freshness */}
        <span className="flex items-center gap-1 text-xs">
          <Circle className="w-2 h-2 fill-current" style={{ color: freshnessColor }} />
          <span style={{ color: 'var(--text-muted)' }}>Live</span>
        </span>

        {/* Alarm Badge */}
        {activeAlarms > 0 && (
          <span className="flex items-center gap-1 text-xs">
            <Bell className="w-3 h-3" style={{ color: 'var(--status-critical)' }} />
            <span style={{ color: 'var(--status-critical)' }}>{activeAlarms}</span>
          </span>
        )}

        {isLoggedIn && (
          <>
            <span className="text-xs" style={{ color: 'var(--text-muted)' }}>{username}</span>
            <button
              onClick={handleLogout}
              className="flex items-center gap-1 text-xs transition-colors"
              style={{ color: 'var(--text-muted)' }}
              title="Logout"
            >
              <LogOut className="w-3.5 h-3.5" />
              Logout
            </button>
          </>
        )}
        <span className="text-xs border rounded px-1.5 py-0.5 font-mono" style={{ color: 'var(--text-muted)', borderColor: 'var(--border-default)' }}>
          v0.1.0
        </span>
      </div>
    </header>
  );
}
