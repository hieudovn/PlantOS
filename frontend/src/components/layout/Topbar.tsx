import { useWorkspace } from "@/lib/WorkspaceContext";
import { useNavigate } from "react-router-dom";
import { LogOut } from "lucide-react";

export function Topbar() {
  const { plantId, setPlantId, plants } = useWorkspace();
  const navigate = useNavigate();
  const username = localStorage.getItem("plantos_user") || "MVP Demo";
  const isLoggedIn = !!localStorage.getItem("plantos_token") || true;

  const handleLogout = () => {
    localStorage.removeItem("plantos_token");
    localStorage.removeItem("plantos_user");
    navigate("/login");
  };

  return (
    <header className="h-14 border-b border-gray-800 flex items-center justify-between px-6 bg-gray-900/50">
      <div className="flex items-center gap-2">
        <span className="text-sm text-gray-400">Workspace:</span>
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
        {isLoggedIn && (
          <>
            <span className="text-xs text-gray-500">{username}</span>
            <button
              onClick={handleLogout}
              className="flex items-center gap-1 text-xs text-gray-500 hover:text-red-400 transition-colors"
              title="Logout"
            >
              <LogOut className="w-3.5 h-3.5" />
              Logout
            </button>
          </>
        )}
        <span className="text-xs text-gray-600">MVP Preview</span>
      </div>
    </header>
  );
}
