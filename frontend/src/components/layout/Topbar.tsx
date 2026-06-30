import { useWorkspace } from "@/lib/WorkspaceContext";

export function Topbar() {
  const { plantId, setPlantId, plants } = useWorkspace();

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
      <div className="text-xs text-gray-600">MVP Preview</div>
    </header>
  );
}
